/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2016 Universita' degli Studi di Napoli Federico II
 *               2016 University of Washington
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
 * Authors:  Stefano Avallone <stavallo@unina.it>
 *           Tom Henderson <tomhend@u.washington.edu>
 *           Pasquale Imputato <p.imputato@gmail.com>
 */

#ifndef IPV4_SRC_DST_PACKET_FILTER_H
#define IPV4_SRC_DST_PACKET_FILTER_H

#include "ns3/object.h"
#include "ns3/packet-filter.h"
#include <map>
#include <tuple>
#include "ns3/ipv4-address.h"

namespace ns3 {

/**
 * \ingroup ipv4
 * \ingroup traffic-control
 *
 * Ipv4SrcDstPacketFilter is the abstract base class for filters defined for IPv4 packets.
 */
class Ipv4SrcDstPacketFilter: public PacketFilter {
public:
  /**
   * \brief Get the type ID.
   * \return the object TypeId
   */
  static TypeId GetTypeId (void);

  Ipv4SrcDstPacketFilter ();

  virtual ~Ipv4SrcDstPacketFilter ();
  void clearAssociationMap();

private:
  virtual bool CheckProtocol (Ptr<QueueDiscItem> item) const;
  virtual int32_t DoClassify (Ptr<QueueDiscItem> item) const;
  std::map<std::tuple<Ipv4Address, Ipv4Address>, uint32_t> *m_map_addr_qnum; // DoClassify is const, so cannot modify internal parameters. To bypass the problem we use pointer.
  
};

} // namespace ns3

#endif /* IPV4_DST_PACKET_FILTER */
