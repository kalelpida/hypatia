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
 * Author: Jens Eirik Saethre  June 2019
 *         Andre Aguas         March 2020
 *         Simon               2020
 * 
 */


#include "ns3/abort.h"
#include "ns3/log.h"
#include "ns3/simulator.h"
#include "ns3/gsl-net-device.h"
#include "ns3/gsl-channel.h"
#include "ns3/queue.h"
#include "ns3/net-device-queue-interface.h"
#include "ns3/config.h"
#include "ns3/packet.h"
#include "ns3/names.h"
#include "ns3/string.h"
#include "ns3/mpi-interface.h"
#include "ns3/mpi-receiver.h"

#include "ns3/rr-queue-disc.h"

#include "ns3/trace-helper.h"
#include "ns3/gsl-helper.h"
#include "ns3/specie.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("GSLHelper");

GSLHelper::GSLHelper (const std::vector<std::pair<uint, std::string>>& nodetypes, std::map<std::string, std::string> tctypes, std::map<std::string, std::map<std::string, std::string>> tcattributes):
m_nodetypes(nodetypes), m_tctypes(tctypes), m_tcattributes(tcattributes)
{
  
  for (auto attr : nodetypes){
    // attr->second : nodetype attr->first : first node of next nodetype
    m_queueFactories[attr.second] = ObjectFactory();
    m_queueFactories[attr.second].SetTypeId ("ns3::DropTailQueue<Packet>");
    m_deviceFactories[attr.second] = ObjectFactory();
    m_deviceFactories[attr.second].SetTypeId ("ns3::GSLNetDevice");
  }
  
  m_channelFactory.SetTypeId ("ns3::GSLChannel");  
}

void 
GSLHelper::SetQueue (std::string nodetype, std::string type,
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
GSLHelper::SetDeviceAttribute (std::string nodetype, std::string n1, const AttributeValue &v1)
{
  m_deviceFactories[nodetype].Set (n1, v1);
}

void 
GSLHelper::SetChannelAttribute (std::string n1, const AttributeValue &v1)
{
  m_channelFactory.Set (n1, v1);
}

NetDeviceContainer 
GSLHelper::Install (NodeContainer satellites, NodeContainer ground_stations, std::vector<std::tuple<int32_t, double>>& node_gsl_if_info)
{

    // Primary channel
    Ptr<GSLChannel> channel = m_channelFactory.Create<GSLChannel> ();

    // All network devices we added
    NetDeviceContainer allNetDevices;

    // Satellite network devices
    for (size_t sid = 0; sid < satellites.GetN(); sid++)  {
        size_t num_ifs = std::get<0>(node_gsl_if_info[sid]);
        for (size_t j = 0; j < num_ifs; j++) {
            allNetDevices.Add(Install(satellites.Get(sid), channel));
        }
    }

    // Ground station network devices
    size_t satellites_offset = satellites.GetN();
    for (size_t gid = 0; gid < ground_stations.GetN(); gid++)  {

        // Node
        Ptr<Node> gs_node = ground_stations.Get(gid);

        // Add interfaces
        size_t num_ifs = std::get<0>(node_gsl_if_info[satellites_offset + gid]);
        for (size_t j = 0; j < num_ifs; j++) {
            allNetDevices.Add(Install(gs_node, channel));
        }

    }

    // The lower bound for the GSL channel must be set to facilitate distributed simulation.
    // However, this is challenging, as delays vary over time based on the movement.
    // As such, for now this delay = lookahead time is set to 0.
    // (see also the Delay attribute in gsl-channel.cc)
    channel->SetAttribute("Delay", TimeValue(Seconds(0)));

    return allNetDevices;
}

Ptr<GSLNetDevice>
GSLHelper::Install (Ptr<Node> node, Ptr<GSLChannel> channel) {

    //choose device type
    std::string nodetype= node->GetObject<Specie>()->GetName();
    /*
    for (auto attr: m_nodetypes){
      if (attr.first > node->GetId()){
        nodetype = attr.second;
        break;
      }
    }*/
    
    NS_ABORT_IF(nodetype.empty());

    // Create device
    Ptr<GSLNetDevice> dev = m_deviceFactories[nodetype].Create<GSLNetDevice>();

    // Set unique MAC address
    dev->SetAddress (Mac48Address::Allocate ());

    // Add device to the node
    node->AddDevice (dev);

    // Set device queue
    Ptr<Queue<Packet> > queue = m_queueFactories[nodetype].Create<Queue<Packet>>();
    dev->SetQueue (queue);

    // Aggregate NetDeviceQueueInterface objects to connect
    // the device queue to the interface (used by traffic control layer)
    auto search = m_tctypes.find(nodetype);
    if (search != m_tctypes.end()){
      // Traffic control helper
      TrafficControlHelper tch_gsl;
      if (m_tcattributes[nodetype].find("ChildQueueDisc")!=m_tcattributes[nodetype].end()){
        tch_gsl.SetRootQueueDisc(m_tctypes[nodetype], "ChildQueueDisc", StringValue(m_tcattributes[nodetype].at("ChildQueueDisc")));
      } else{
        tch_gsl.SetRootQueueDisc(m_tctypes[nodetype]);
      }
      //, "MaxSize", QueueSizeValue(QueueSize("100p")), "ChildQueueDisc", StringValue("ns3::ITbfQueueDisc"));//ns3::ITbfQueueDisc, ns3::FifoQueueDisc
      
      //m_tch_gsl.SetRootQueueDisc("ns3::FqCoDelQueueDisc", "DropBatchSize", UintegerValue(1), "Perturbation", UintegerValue(256));
      Ptr<NetDeviceQueueInterface> ndqi = CreateObject<NetDeviceQueueInterface> ();
      ndqi->GetTxQueue (0)->ConnectQueueTraces (queue);//if connected, packets will never be dropped in the netdevice, but before. 
      dev->AggregateObject (ndqi);
      QueueDiscContainer qd = tch_gsl.Install(dev);
      for (const auto&  pair : m_tcattributes[nodetype]){
        if (pair.first=="ChildQueueDisc"){
          continue;
        }
        size_t i;
        std::string avant, suite(pair.second);
        do {
          i=suite.find(' ');
          avant = suite.substr(0, i);
          suite = suite.substr(i+1);
        } while (i==0);
        if ( avant ==  "QueueSize" ){
            if (pair.first.rfind("Child", 0) == 0) { // pos=0 limits the search to the prefix
            // s starts with prefix
            //child queue factory, for RRQueue
              qd.Get(0)->GetObject<RRQueueDisc>()->GetChildQueueFactory().Set(pair.first.substr(5), QueueSizeValue(QueueSize(suite)));
            } else{
              qd.Get(0)->SetAttribute(pair.first, QueueSizeValue(QueueSize(suite)));
            }
        } else if ( avant == "String"){
            if (pair.first.rfind("Child", 0) == 0) {
              qd.Get(0)->GetObject<RRQueueDisc>()->GetChildQueueFactory().Set(pair.first.substr(5),  StringValue(suite));
            } else{
              qd.Get(0)->SetAttribute(pair.first,  StringValue(suite));
            }
        } else if ( avant == "DataRate"){
            if (pair.first.rfind("Child", 0) == 0) {
              qd.Get(0)->GetObject<RRQueueDisc>()->GetChildQueueFactory().Set(pair.first.substr(5),  DataRateValue(DataRate(suite)));
            } else{
              qd.Get(0)->SetAttribute(pair.first,  DataRateValue(DataRate(suite)));
            }
        } else if ( avant == "Uinteger"){
            if (pair.first.rfind("Child", 0) == 0) {
              qd.Get(0)->GetObject<RRQueueDisc>()->GetChildQueueFactory().Set(pair.first.substr(5),  UintegerValue(std::stoul(suite)));
            } else{
              qd.Get(0)->SetAttribute(pair.first,  UintegerValue(std::stoul(suite)));
            }
        } else {
          NS_ABORT_MSG("Soucis avec attribut " << pair.first << " type non reconnu");
        }
      }
    }
        
    

    // Aggregate MPI receivers // TODO: Why?
    Ptr<MpiReceiver> mpiRec = CreateObject<MpiReceiver> ();
    mpiRec->SetReceiveCallback (MakeCallback (&GSLNetDevice::Receive, dev));
    dev->AggregateObject(mpiRec);

    // Attach to channel
    dev->Attach (channel);

    return dev;
}


} // namespace ns3
