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

#ifndef FQ_RR_FQUEUE_DISC
#define FQ_RR_FQUEUE_DISC

#include "ns3/queue-disc.h"
#include "ns3/object-factory.h"
#include "ipv4-dst-packet-filter.h"
#include "ns3/rr-queue-disc.h" // for UserFlow
#include <vector>
#include <algorithm>


namespace ns3 {


/**
 * \ingroup traffic-control
 *
 * \brief A Fq packet queue disc
 */
class RRFQueueDisc : public RRQueueDisc {
public:
  /**
   * \brief Get the type ID.
   * \return the object TypeId
   */
  static TypeId GetTypeId (void);
  /**
   * \brief RRFQueueDisc constructor
   */
  RRFQueueDisc ();

  virtual ~RRFQueueDisc ();

private:
  virtual Ptr<QueueDiscItem> DoDequeue (void);// a packet-size fair dequeue
};

} // namespace ns3

#endif /* FQ_RR_FQUEUE_DISC */

