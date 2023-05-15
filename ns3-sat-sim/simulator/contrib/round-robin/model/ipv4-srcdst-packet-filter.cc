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

#include "ns3/log.h"
#include "ns3/enum.h"
#include "ns3/uinteger.h"
#include "ns3/tcp-header.h"
#include "ns3/udp-header.h"
#include "ns3/ipv4-queue-disc-item.h"
#include "ipv4-srcdst-packet-filter.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("Ipv4SrcDstPacketFilter");

NS_OBJECT_ENSURE_REGISTERED (Ipv4SrcDstPacketFilter);

TypeId 
Ipv4SrcDstPacketFilter::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::Ipv4SrcDstPacketFilter")
    .SetParent<PacketFilter> ()
    .SetGroupName ("Internet")
  ;
  return tid;
}

Ipv4SrcDstPacketFilter::Ipv4SrcDstPacketFilter ()
{
  NS_LOG_FUNCTION (this);
  m_map_addr_qnum =  new std::map<std::tuple<Ipv4Address, Ipv4Address>, uint32_t>;
}

Ipv4SrcDstPacketFilter::~Ipv4SrcDstPacketFilter()
{
  NS_LOG_FUNCTION (this);
  delete m_map_addr_qnum;
}

void
Ipv4SrcDstPacketFilter::clearAssociationMap(){
  m_map_addr_qnum->clear();
}

bool
Ipv4SrcDstPacketFilter::CheckProtocol (Ptr<QueueDiscItem> item) const
{
  NS_LOG_FUNCTION (this << item);
  return (DynamicCast<Ipv4QueueDiscItem> (item) != 0);
}

int32_t Ipv4SrcDstPacketFilter::DoClassify (Ptr<QueueDiscItem> item) const{
  Ptr<Ipv4QueueDiscItem> ipv4item = DynamicCast<Ipv4QueueDiscItem> (item);
  if (ipv4item == 0){
    return PacketFilter::PF_NO_MATCH;
  }

  Ipv4Address addr_src = ipv4item->GetHeader().GetSource();
  Ipv4Address addr_dst = ipv4item->GetHeader().GetDestination();
  /*
  TcpHeader tcpheader;
  UdpHeader udpheader;
  uint8_t proto = ipv4item->GetHeader().GetProtocol();
  uint16_t src_port, dst_port;
  if(proto==6){
    ipv4item->GetPacket()->PeekHeader(tcpheader);
    src_port = tcpheader.GetSourcePort();
    dst_port = tcpheader.GetDestinationPort();
  } else if (proto==17){
    ipv4item->GetPacket()->PeekHeader(udpheader);
    src_port = udpheader.GetSourcePort();
    dst_port = udpheader.GetDestinationPort();
  } else {
    NS_ABORT_MSG("proto not recognised: " << proto);
  }
  */
  auto cle = std::make_tuple(addr_src, addr_dst);
  auto it = m_map_addr_qnum->find(cle);
  if (it == std::end(*m_map_addr_qnum)){
    uint32_t num = m_map_addr_qnum->size();
    m_map_addr_qnum->insert(std::make_pair(cle, num));
    return num;
  } else {
    return it->second;
  }


}

// ------------------------------------------------------------------------- //


} // namespace ns3
