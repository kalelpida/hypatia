/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2008 INRIA
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Author: Mathieu Lacage <mathieu.lacage@sophia.inria.fr>
 * (based on point-to-point helper)
 * Author: Andre Aguas         March 2020
 *         Simon               2020
 */


#include "ns3/abort.h"
#include "ns3/log.h"
#include "ns3/simulator.h"
#include "ns3/point-to-point-laser-net-device.h"
#include "ns3/point-to-point-laser-channel.h"
#include "ns3/point-to-point-laser-remote-channel.h"
#include "ns3/queue.h"
#include "ns3/net-device-queue-interface.h"
#include "ns3/config.h"
#include "ns3/packet.h"
#include "ns3/names.h"
#include "ns3/string.h"
#include "ns3/mpi-interface.h"
#include "ns3/mpi-receiver.h"

#include "ns3/trace-helper.h"
#include "point-to-point-laser-helper.h"
#include "ns3/specie.h"
#include "ns3/traffic-control-helper.h"

#include "ns3/device-factory-helper.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("PointToPointLaserHelper");

PointToPointLaserHelper::PointToPointLaserHelper(const std::map<std::string, std::map<std::string, std::string>> node_if_params): 
  m_node_if_params(node_if_params)
{
  for (auto attr : node_if_params){
    // attr->second : nodetype attr->first : first node of next nodetype
    m_queueFactories[attr.first] = ObjectFactory();
    m_queueFactories.at(attr.first).SetTypeId ("ns3::DropTailQueue<Packet>");
    m_queueFactories.at(attr.first).Set("MaxSize", QueueSizeValue(QueueSize(m_node_if_params.at(attr.first).at("devQMaxSize"))));
    m_deviceFactories[attr.first] = ObjectFactory();
    m_deviceFactories.at(attr.first).SetTypeId ("ns3::PointToPointLaserNetDevice");
    setObjFactoryParams(m_deviceFactories.at(attr.first), attr.second);
  }
  m_channelFactory.SetTypeId ("ns3::PointToPointLaserChannel");
  m_remoteChannelFactory.SetTypeId ("ns3::PointToPointLaserRemoteChannel");
}

void 
PointToPointLaserHelper::SetQueue (std::string nodetype, std::string type,
                     std::string n1, const AttributeValue &v1,
                     std::string n2, const AttributeValue &v2,
                     std::string n3, const AttributeValue &v3,
                     std::string n4, const AttributeValue &v4)
{
  QueueBase::AppendItemTypeIfNotPresent (type, "Packet");

  m_queueFactories[nodetype].SetTypeId (type);
  m_queueFactories[nodetype].Set (n1, v1);
  m_queueFactories[nodetype].Set (n2, v2);
  m_queueFactories[nodetype].Set (n3, v3);
  m_queueFactories[nodetype].Set (n4, v4);
}

void 
PointToPointLaserHelper::SetChannelAttribute (std::string n1, const AttributeValue &v1)
{
  m_channelFactory.Set (n1, v1);
  m_remoteChannelFactory.Set (n1, v1);
}

NetDeviceContainer 
PointToPointLaserHelper::Install (NodeContainer c)
{
  NS_ASSERT (c.GetN () == 2);
  return Install (c.Get (0), c.Get (1));
}

NetDeviceContainer 
PointToPointLaserHelper::Install (Ptr<Node> a, Ptr<Node> b)
{
  // set the initial delay of the channel as the delay estimation for the lookahead of the
  // distributed scheduler
  //choose device type
  std::string nodetypea= a->GetObject<Specie>()->GetName();
  std::string nodetypeb= b->GetObject<Specie>()->GetName();

  Ptr<MobilityModel> aMobility = a->GetObject<MobilityModel>();
  Ptr<MobilityModel> bMobility = b->GetObject<MobilityModel>();
  double propagation_speed(299792458.0);
  double distance = aMobility->GetDistanceFrom (bMobility);
  double delay = distance / propagation_speed;
  SetChannelAttribute("Delay", StringValue(std::to_string(delay) + "s"));

  NetDeviceContainer container;

  Ptr<PointToPointLaserNetDevice> devA = m_deviceFactories[nodetypea].Create<PointToPointLaserNetDevice> ();
  devA->SetAddress (Mac48Address::Allocate ());
  devA->SetDestinationNode(b);
  a->AddDevice (devA);
  Ptr<Queue<Packet> > queueA = m_queueFactories[nodetypea].Create<Queue<Packet> > ();
  devA->SetQueue (queueA);
  Ptr<PointToPointLaserNetDevice> devB = m_deviceFactories[nodetypeb].Create<PointToPointLaserNetDevice> ();
  devB->SetAddress (Mac48Address::Allocate ());
  devB->SetDestinationNode(a);
  b->AddDevice (devB);
  Ptr<Queue<Packet> > queueB = m_queueFactories[nodetypeb].Create<Queue<Packet> > ();
  devB->SetQueue (queueB);

  //things related to queueing, netdev queue interface, traffic control
  SetDevParam(devA, a->GetObject<Specie>()->GetName());
  SetDevParam(devB, b->GetObject<Specie>()->GetName());

  // Distributed mode
  NS_ABORT_MSG_IF(MpiInterface::IsEnabled(), "Distributed mode is not currently supported for point-to-point lasers.");

  // Distributed mode is not currently supported, enable the below if it is:
//  // If MPI is enabled, we need to see if both nodes have the same system id
//  // (rank), and the rank is the same as this instance.  If both are true,
//  //use a normal p2p channel, otherwise use a remote channel
//  bool useNormalChannel = true;
//  Ptr<PointToPointLaserChannel> channel = 0;
//
//  if (MpiInterface::IsEnabled ()) {
//      uint32_t n1SystemId = a->GetSystemId ();
//      uint32_t n2SystemId = b->GetSystemId ();
//      uint32_t currSystemId = MpiInterface::GetSystemId ();
//      if (n1SystemId != currSystemId || n2SystemId != currSystemId) {
//          useNormalChannel = false;
//      }
//  }
//  if (useNormalChannel) {
//    channel = m_channelFactory.Create<PointToPointLaserChannel> ();
//  }
//  else {
//    channel = m_remoteChannelFactory.Create<PointToPointLaserRemoteChannel>();
//    Ptr<MpiReceiver> mpiRecA = CreateObject<MpiReceiver> ();
//    Ptr<MpiReceiver> mpiRecB = CreateObject<MpiReceiver> ();
//    mpiRecA->SetReceiveCallback (MakeCallback (&PointToPointLaserNetDevice::Receive, devA));
//    mpiRecB->SetReceiveCallback (MakeCallback (&PointToPointLaserNetDevice::Receive, devB));
//    devA->AggregateObject (mpiRecA);
//    devB->AggregateObject (mpiRecB);
//  }

  // Create and attach channel
  Ptr<PointToPointLaserChannel> channel = m_channelFactory.Create<PointToPointLaserChannel> ();
  devA->Attach (channel);
  devB->Attach (channel);
  container.Add (devA);
  container.Add (devB);

  return container;
}

void 
PointToPointLaserHelper::SetDevParam(Ptr<PointToPointLaserNetDevice> dev, const std::string& nodetype)
{
  // Aggregate NetDeviceQueueInterface objects to connect
    // the device queue to the interface (used by traffic control layer)
    const std::map<std::string, std::string> paramap = m_node_if_params.at(nodetype);
    auto search = paramap.find("QueueDisc");
    if (search != paramap.end()){
      // Traffic control helper
      TrafficControlHelper tch_gsl;
      if (paramap.find("ChildQueueDisc")!=paramap.end()){
        tch_gsl.SetRootQueueDisc(paramap.at("QueueDisc"), "ChildQueueDisc", StringValue(paramap.at("ChildQueueDisc")));
      } else{
        tch_gsl.SetRootQueueDisc(paramap.at("QueueDisc"));
      }
      //, "MaxSize", QueueSizeValue(QueueSize("100p")), "ChildQueueDisc", StringValue("ns3::ITbfQueueDisc"));//ns3::ITbfQueueDisc, ns3::FifoQueueDisc
      
      //m_tch_gsl.SetRootQueueDisc("ns3::FqCoDelQueueDisc", "DropBatchSize", UintegerValue(1), "Perturbation", UintegerValue(256));
      Ptr<NetDeviceQueueInterface> ndqi = CreateObject<NetDeviceQueueInterface> ();
      ndqi->GetTxQueue (0)->ConnectQueueTraces (dev->GetQueue());//if connected, packets will never be dropped in the netdevice, but before. 
      dev->AggregateObject (ndqi);
      QueueDiscContainer qd = tch_gsl.Install(dev);
      setQdiscParams(qd, paramap);
    }
}
} // namespace ns3
