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
#include "rr-fqueue-disc.h"
#include "ns3/net-device-queue-interface.h"
#include "ns3/simulator.h" // for schedule


namespace ns3 {

static bool myGreater(Ptr<UserFlow> x, Ptr<UserFlow> y){
    return x->GetPrio() > y->GetPrio();
}

NS_LOG_COMPONENT_DEFINE ("RRFQueueDisc");

NS_OBJECT_ENSURE_REGISTERED (RRFQueueDisc);

TypeId RRFQueueDisc::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::RRFQueueDisc")
    .SetParent<RRQueueDisc> ()
    .SetGroupName ("TrafficControl")
    .AddConstructor<RRFQueueDisc> ()
  ;
  return tid;
}

RRFQueueDisc::RRFQueueDisc ()
  :RRQueueDisc()
{
  NS_LOG_FUNCTION (this);
}

RRFQueueDisc::~RRFQueueDisc ()
{
  NS_LOG_FUNCTION (this);
}


Ptr<QueueDiscItem>
RRFQueueDisc::DoDequeue (void)
{
  NS_LOG_FUNCTION (this);

  Ptr<QueueDiscItem> item = 0;
  Ptr<QueueDisc> qd = 0;
  Ptr<UserFlow> flow;
  m_waiting = true;
  std::make_heap(m_flowsDequeue.begin(), m_flowsDequeue.end(), myGreater); // the higher the flow index, the lower the priority
  bool premflow=true;
  for (auto dernier=m_flowsDequeue.end(); dernier!=m_flowsDequeue.begin(); dernier--){
    std::pop_heap(m_flowsDequeue.begin(), dernier, myGreater);
    flow=m_flowsDequeue.back();
    qd = flow->GetQueueDisc();
    if (m_flow_it_id>=m_flowsDequeue.size()){
      m_flow_it_id=0;
    }
    uint32_t flowprio = flow->GetPrio();
    if (qd->GetCurrentSize().GetValue() != 0){
      if (premflow && flowprio ){
        /* reduce values of all flows. Two reasons:
        1/ Avoid exceeding the maximal uint index value 
        2/ A non active flow should not earn priority compared to an active one. 
        This to avoid that a flow restarts after a long period and gets the priority because it was considered as 'waiting'
        */
        for (auto x: m_flowsDequeue){
            uint32_t xprio = x->GetPrio();
            if ( xprio > 0){
                x->SetPrio(xprio - std::min(flowprio, xprio));
            }
        }
      }
      premflow=false;
      item = qd->Dequeue();
      if (item!=0){
        m_waiting = false;
        flow->SetPrio(flowprio+item->GetSize());
        break;
      }
    }
  }
  return item;
}

} // namespace ns3

