/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2016 Universita' degli Studi di Napoli Federico II
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
 * Authors: Pasquale Imputato <p.imputato@gmail.com>
 *          Stefano Avallone <stefano.avallone@unina.it>
*/

#include "ns3/log.h"
#include "ns3/string.h"
#include "ns3/queue.h"
#include "rr-queue-disc.h"
#include "ns3/net-device-queue-interface.h"
#include "ns3/simulator.h" // for schedule

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("RRQueueDisc");

NS_OBJECT_ENSURE_REGISTERED (UserFlow);

TypeId UserFlow::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::UserFlow")
    .SetParent<QueueDiscClass> ()
    .SetGroupName ("TrafficControl")
    .AddConstructor<UserFlow> ()
  ;
  return tid;
}

UserFlow::UserFlow ()
  : m_status (EMPTY),
    m_index (0)
{
  NS_LOG_FUNCTION (this);
}

UserFlow::~UserFlow ()
{
  NS_LOG_FUNCTION (this);
}

void
UserFlow::SetStatus (FlowStatus status)
{
  NS_LOG_FUNCTION (this);
  m_status = status;
}

UserFlow::FlowStatus
UserFlow::GetStatus (void) const
{
  NS_LOG_FUNCTION (this);
  return m_status;
}

void
UserFlow::SetIndex (uint32_t index)
{
  NS_LOG_FUNCTION (this);
  m_index = index;
}

uint32_t
UserFlow::GetIndex (void) const
{
  return m_index;
}



NS_OBJECT_ENSURE_REGISTERED (RRQueueDisc);

TypeId RRQueueDisc::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::RRQueueDisc")
    .SetParent<QueueDisc> ()
    .SetGroupName ("TrafficControl")
    .AddConstructor<RRQueueDisc> ()
    .AddAttribute ("MaxSize",
                   "The maximum number of packets accepted by this queue disc",
                   QueueSizeValue (QueueSize ("10240p")),
                   MakeQueueSizeAccessor (&QueueDisc::SetMaxSize,
                                          &QueueDisc::GetMaxSize),
                   MakeQueueSizeChecker ())
    .AddAttribute("ChildQueueDisc", 
                    "The q disc to be applied on child queues",
                    StringValue("ns3::FifoQueueDisc"),
                    MakeStringAccessor(&RRQueueDisc::GetChildQDiscType, &RRQueueDisc::SetChildQDiscType),
                    MakeStringChecker())
  ;
  return tid;
}

RRQueueDisc::RRQueueDisc ()
  : QueueDisc (QueueDiscSizePolicy::MULTIPLE_QUEUES), m_flow_it_id(0), m_waiting(false)
{
  NS_LOG_FUNCTION (this);
  m_filter = CreateObject<Ipv4DstPacketFilter> ();
  AddPacketFilter(m_filter);
}

RRQueueDisc::~RRQueueDisc ()
{
  NS_LOG_FUNCTION (this);
}


bool
RRQueueDisc::DoEnqueue (Ptr<QueueDiscItem> item)
{
  NS_LOG_FUNCTION (this << item);

  NS_ASSERT(GetNPacketFilters () == 1);
  int32_t ret = Classify (item);

  if (ret == PacketFilter::PF_NO_MATCH){
      NS_LOG_ERROR ("No filter has been able to classify this packet, drop it.");
      DropBeforeEnqueue (item, UNCLASSIFIED_DROP);
      return false;
  } 
  size_t idflow = static_cast<size_t>(ret);
  bool result;
  if (idflow < m_flows.size()) {
    if (m_flows[idflow]->GetStatus() == UserFlow::EMPTY){
      m_flows[idflow]->SetStatus(UserFlow::ACTIVE);
    }
    result = m_flows[idflow]->GetQueueDisc()->Enqueue(item);
  } else if (idflow == m_flows.size()) {
      Ptr<UserFlow> flow = m_flowFactory.Create<UserFlow> ();
      Ptr<QueueDisc> qd = m_queueDiscFactory.Create<QueueDisc> ();
      qd->Initialize ();
      flow->SetQueueDisc (qd);
      flow->SetIndex (idflow);
      AddQueueDiscClass (flow);
      m_flows.push_back(flow); // cheating, to access more easily to qdisc classes than via QueueDisc Class methods. m_classes attribute is private
      result=m_flows[idflow]->GetQueueDisc()->Enqueue(item);
      m_flows[idflow]->SetStatus(UserFlow::ACTIVE);
  } else {
    DropBeforeEnqueue (item, UNCLASSIFIED_DROP);
    return false;
  }

  NS_LOG_DEBUG ("Packet enqueued into flow " << idflow << " success: " << result);
  //enqueue failed ? 
  // DropBeforeEnqueue isalready called thanks to AddQueueDiscClass setting up the callbacks
  return result;
}

Ptr<QueueDiscItem>
RRQueueDisc::DoDequeue (void)
{
  NS_LOG_FUNCTION (this);

  Ptr<QueueDiscItem> item = 0;
  Ptr<QueueDisc> qd = 0;
  Ptr<UserFlow> flow;
  m_waiting = true;

  for (size_t i=0; i<m_flows.size(); i++){
    flow=m_flows[m_flow_it_id];
    qd = flow->GetQueueDisc();
    //set for next iteration
    m_flow_it_id++;
    if (m_flow_it_id>=m_flows.size()){
      m_flow_it_id=0;
    }
    if (flow->GetStatus() == UserFlow::ACTIVE){
      item = qd->Dequeue();
      if (qd->GetCurrentSize().GetValue() == 0){
        flow->SetStatus(UserFlow::EMPTY);
      }
      if (item!=0){
        m_waiting = false;
        break;
      }
    }
  }
  return item;
}

bool
RRQueueDisc::CheckConfig (void)
{
  NS_LOG_FUNCTION (this);
  if (GetNQueueDiscClasses () > 0)
    {
      NS_LOG_ERROR ("RRQueueDisc cannot have classes");
      return false;
    }
  
  if (GetNPacketFilters () != 1)
    {
      NS_LOG_ERROR ("RRQueueDisc should have one filter");
      return false;
    }
  
  if (GetNInternalQueues () > 0)
    {
      NS_LOG_ERROR ("RRQueueDisc cannot have internal queues");
      return false;
    }
  return true;
}

void
RRQueueDisc::InitializeParams (void)
{
  NS_LOG_FUNCTION (this);

  m_queueDiscFactory.Set ("MaxSize", QueueSizeValue (GetMaxSize ()));
  m_flowFactory.SetTypeId ("ns3::UserFlow");
  if (m_child_qdisc_str.find("ITbfQueueDisc") != std::string::npos){
    //call back RRQueueDisc when a TBF queue is ready to transmit. Used when the DoDequeue method was called once, but TBF limited
     m_queueDiscFactory.Set ("MasterRun", CallbackValue(MakeCallback(&RRQueueDisc::WaitedRun, this)));
  }
}
ObjectFactory& 
RRQueueDisc::GetChildQueueFactory(){
    return m_queueDiscFactory;
}

void 
RRQueueDisc::Clean(){
  NS_LOG_FUNCTION(this);
  m_filter->clearAssociationMap();
  m_flows.clear();
  m_flow_it_id = 0;
}

void 
RRQueueDisc::WaitedRun(){
  if (m_waiting){
    Run();
  }
}

void 
RRQueueDisc::SetChildQDiscType(const std::string& str){
  m_child_qdisc_str = str;
  m_queueDiscFactory.SetTypeId(str); // Too late in InitializeParams, too early in RRQueueDisc. This setter is called between the two
}

std::string 
RRQueueDisc::GetChildQDiscType() const{
  return m_child_qdisc_str;
}

} // namespace ns3

