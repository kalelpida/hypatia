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

#ifndef FQ_RR_QUEUE_DISC
#define FQ_RR_QUEUE_DISC

#include "ns3/queue-disc.h"
#include "ns3/object-factory.h"
#include "ipv4-dst-packet-filter.h"
#include <vector>
#include <map>

namespace ns3 {

/**
 * \ingroup traffic-control
 *
 * \brief A flow queue used by the FqCoDel queue disc
 */

class UserFlow : public QueueDiscClass {
public:
  /**
   * \brief Get the type ID.
   * \return the object TypeId
   */
  static TypeId GetTypeId (void);
  /**
   * \brief UserFlow constructor
   */
  UserFlow ();

  virtual ~UserFlow ();
  void SetIndex (uint32_t index);
  /**
   * \brief Get the index of this flow
   * \return the index of this flow
   */
  uint32_t GetIndex (void) const;

  /**
   * \brief Set the priority of this flow
   * \param prio the new priority of this flow
   *
  */
  void SetPrio (uint32_t prio);
  /**
   * \brief Get the priority of this flow
   * \return the priority of this flow
   */
  uint32_t GetPrio (void) const;

private:
  uint32_t m_prio;     //!< the index for this flow
  uint32_t m_index;     //!< the index for this flow
};


/**
 * \ingroup traffic-control
 *
 * \brief A Fq packet queue disc
 */
class RRQueueDisc : public QueueDisc {
public:
  /**
   * \brief Get the type ID.
   * \return the object TypeId
   */
  static TypeId GetTypeId (void);
  /**
   * \brief RRQueueDisc constructor
   */
  RRQueueDisc ();

  virtual ~RRQueueDisc ();

  void Clean();
  void WaitedRun();

  
  ObjectFactory& GetChildQueueFactory();
  void SetChildQDiscType(const std::string& str);
  std::string GetChildQDiscType() const;

  // Reasons for dropping packets
  static constexpr const char* UNCLASSIFIED_DROP = "Unclassified drop";  //!< No packet filter able to classify packet
  static constexpr const char* OVERLIMIT_DROP = "Overlimit drop";        //!< Overlimit dropped packets

protected:
  virtual bool DoEnqueue (Ptr<QueueDiscItem> item);
  virtual Ptr<QueueDiscItem> DoDequeue (void);
  virtual bool CheckConfig (void);
  virtual void InitializeParams (void);

  std::vector<Ptr<UserFlow>> m_flowsDequeue;          //!< The liste of flows, used to dequeue packets
  std::map<uint32_t, Ptr<UserFlow>> m_flowsEnqueue;    //!< Map with the index of class for each flow. Helps tp enqueue a packet
  // TODO Think about deleting unused flows. Update filter 
  size_t m_flow_it_id;                                     //!< The associated iterator
  Ptr<Ipv4DstPacketFilter> m_filter;                      //!< The ipv4 filter
  bool m_waiting;                                         //!< the net device has called

  std::string m_child_qdisc_str;                              //<! child qdisc

  ObjectFactory m_flowFactory;         //!< Factory to create a new flow
  ObjectFactory m_queueDiscFactory;    //!< Factory to create a new queue
};

} // namespace ns3

#endif /* FQ_RR_QUEUE_DISC */

