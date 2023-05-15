/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2010 Georgia Institute of Technology
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
 * Author: Paul
 * Author: Simon
 * Adapted from BulkSendApplication by:
 * Author: George F. Riley <riley@ece.gatech.edu>
 */

#ifndef TCP_PACED_FLOW_SEND_APPLICATION_H
#define TCP_PACED_FLOW_SEND_APPLICATION_H

#include "ns3/address.h"
#include "ns3/application.h"
#include "ns3/event-id.h"
#include "ns3/ptr.h"
#include "ns3/string.h"
#include "ns3/traced-callback.h"
//#include "ns3/topology-satellite-network.h"
#include "tcp-flow-send-application.h"
#include "ns3/topology.h"
#include "ns3/ipv4.h"
#include "ns3/data-rate.h"

namespace ns3 {

class Address;
class Socket;

class TcpPacedFlowSendApplication : public TcpFlowSendApplication
{
public:
  static TypeId GetTypeId (void);

  TcpPacedFlowSendApplication ();

  virtual ~TcpPacedFlowSendApplication ();

protected:
  //virtual void StartApplication (void);    // Called at time specified by Start
  virtual void StopApplication (void);     // Called at time specified by Stop

  /**
   * Send data until the L4 transmission buffer is full.
   */
  void SendData ();
  void EndPacing();

  // Pacing
  bool m_pacing;                    //!< pacing activated
  bool m_sending_ongoing;           //!< true when send buffer is not full
  DataRate m_bps;                   //!< pacing Datarate
  EventId m_endPacingEvent;    //!< event calling unpacing method

};

} // namespace ns3

#endif /* TCP_PACED_FLOW_SEND_APPLICATION_H */
