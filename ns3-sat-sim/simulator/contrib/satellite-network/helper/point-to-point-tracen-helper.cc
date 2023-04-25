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
 */

#include "ns3/abort.h"
#include "ns3/log.h"
#include "ns3/simulator.h"
#include "ns3/point-to-point-tracen-net-device.h"
#include "ns3/point-to-point-tracen-channel.h"
#include "ns3/string.h"
#include "ns3/queue.h"
#include "ns3/net-device-queue-interface.h"
#include "ns3/config.h"
#include "ns3/packet.h"
#include "ns3/names.h"
#include "ns3/specie.h"
#include "ns3/traffic-control-helper.h"
#include "ns3/device-factory-helper.h"


#ifdef NS3_MPI
#include "ns3/mpi-interface.h"
#include "ns3/mpi-receiver.h"
#include "ns3/point-to-point-tracen-remote-channel.h"
#endif

#include "point-to-point-tracen-helper.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("PointToPointTracenHelper");

PointToPointTracenHelper::PointToPointTracenHelper(const std::map<std::string, std::map<std::string, std::string>> node_if_params, const std::map<std::string, std::string> channel_params): 
  m_node_if_params(node_if_params)
{
  for (auto attr : node_if_params){
    // attr->second : nodetype attr->first : first node of next nodetype
    m_queueFactories[attr.first] = ObjectFactory();
    m_queueFactories.at(attr.first).SetTypeId ("ns3::DropTailQueue<Packet>");
    m_deviceFactories[attr.first] = ObjectFactory();
    m_deviceFactories.at(attr.first).SetTypeId ("ns3::PointToPointTracenNetDevice");
    setObjFactoryParams(m_deviceFactories.at(attr.first), attr.second);
  }
  
  m_channelFactory.SetTypeId ("ns3::PointToPointTracenChannel");
  setObjFactoryParams(m_channelFactory, channel_params);
#ifdef NS3_MPI
  m_remoteChannelFactory.SetTypeId ("ns3::PointToPointTracenRemoteChannel");
#endif
}

void 
PointToPointTracenHelper::SetQueue (std::string nodetype, std::string type,
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
PointToPointTracenHelper::SetChannelAttribute (std::string n1, const AttributeValue &v1)
{
  m_channelFactory.Set (n1, v1);
#ifdef NS3_MPI
  m_remoteChannelFactory.Set (n1, v1);
#endif
}

NetDeviceContainer 
PointToPointTracenHelper::Install (NodeContainer c)
{
  NS_ASSERT (c.GetN () == 2);
  return Install (c.Get (0), c.Get (1));
}

NetDeviceContainer 
PointToPointTracenHelper::Install (Ptr<Node> a, Ptr<Node> b)
{
  
  std::string nodetypea= a->GetObject<Specie>()->GetName();
  std::string nodetypeb= b->GetObject<Specie>()->GetName();
  
  NetDeviceContainer container;

  Ptr<PointToPointTracenNetDevice> devA = m_deviceFactories[nodetypea].Create<PointToPointTracenNetDevice> ();
  devA->SetAddress (Mac48Address::Allocate ());
  devA->SetDestinationNode(b);
  a->AddDevice (devA);
  Ptr<Queue<Packet> > queueA = m_queueFactories[nodetypea].Create<Queue<Packet> > ();
  devA->SetQueue (queueA);
  Ptr<PointToPointTracenNetDevice> devB = m_deviceFactories[nodetypeb].Create<PointToPointTracenNetDevice> ();
  devB->SetAddress (Mac48Address::Allocate ());
  devB->SetDestinationNode(a);
  b->AddDevice (devB);
  Ptr<Queue<Packet> > queueB = m_queueFactories[nodetypeb].Create<Queue<Packet> > ();
  devB->SetQueue (queueB);

  //things related to queueing, netdev queue interface, traffic control
  SetDevParam(devA, a->GetObject<Specie>()->GetName());
  SetDevParam(devB, b->GetObject<Specie>()->GetName());

  Ptr<PointToPointTracenChannel> channel = 0;

 // Distributed mode is not currently supported, enable the below if it is:
  // If MPI is enabled, we need to see if both nodes have the same system id 
  // (rank), and the rank is the same as this instance.  If both are true, 
  // use a normal p2p channel, otherwise use a remote channel
//#ifdef NS3_MPI
//  bool useNormalChannel = true;
//  if (MpiInterface::IsEnabled ())
//    {
//      uint32_t n1SystemId = a->GetSystemId ();
//      uint32_t n2SystemId = b->GetSystemId ();
//      uint32_t currSystemId = MpiInterface::GetSystemId ();
//      if (n1SystemId != currSystemId || n2SystemId != currSystemId) 
//        {
//          useNormalChannel = false;
//        }
//    }
//  if (useNormalChannel)
//    {
//      channel = m_channelFactory.Create<PointToPointTracenChannel> ();
//    }
//  else
//    {
//      channel = m_remoteChannelFactory.Create<PointToPointTracenRemoteChannel> ();
//      Ptr<MpiReceiver> mpiRecA = CreateObject<MpiReceiver> ();
//      Ptr<MpiReceiver> mpiRecB = CreateObject<MpiReceiver> ();
//      mpiRecA->SetReceiveCallback (MakeCallback (&PointToPointTracenNetDevice::Receive, devA));
//      mpiRecB->SetReceiveCallback (MakeCallback (&PointToPointTracenNetDevice::Receive, devB));
//      devA->AggregateObject (mpiRecA);
//      devB->AggregateObject (mpiRecB);
//    }
//#else
  channel = m_channelFactory.Create<PointToPointTracenChannel> ();
//#endif

  devA->Attach (channel);
  devB->Attach (channel);
  container.Add (devA);
  container.Add (devB);

  return container;
}

NetDeviceContainer 
PointToPointTracenHelper::Install (Ptr<Node> a, std::string bName)
{
  Ptr<Node> b = Names::Find<Node> (bName);
  return Install (a, b);
}

NetDeviceContainer 
PointToPointTracenHelper::Install (std::string aName, Ptr<Node> b)
{
  Ptr<Node> a = Names::Find<Node> (aName);
  return Install (a, b);
}

NetDeviceContainer 
PointToPointTracenHelper::Install (std::string aName, std::string bName)
{
  Ptr<Node> a = Names::Find<Node> (aName);
  Ptr<Node> b = Names::Find<Node> (bName);
  return Install (a, b);
}

void PointToPointTracenHelper::SetDevParam(Ptr<PointToPointTracenNetDevice> dev, const std::string& nodetype)
{
  // Aggregate NetDeviceQueueInterface objects to connect
    // the device queue to the interface (used by traffic control layer)

    const std::map<std::string, std::string> paramap = m_node_if_params.at(nodetype);
    auto search = paramap.find("QueueDisc");
    if (search != paramap.end()){
      // Traffic control helper
      TrafficControlHelper tch_gsl;
      if (paramap.find("ChildQueueDisc")!=paramap.end()){
        tch_gsl.SetRootQueueDisc(search->second, "ChildQueueDisc", StringValue(paramap.at("ChildQueueDisc")));
      } else{
        tch_gsl.SetRootQueueDisc(search->second);
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
