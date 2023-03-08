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
 * Author: Simon
 * Adapted from BulkSendApplication by:
 * Author: George F. Riley <riley@ece.gatech.edu>
 */

#include "ns3/log.h"
#include "ns3/address.h"
#include "ns3/node.h"
#include "ns3/nstime.h"
#include "ns3/socket.h"
#include "ns3/string.h"
#include "ns3/simulator.h"
#include "ns3/socket-factory.h"
#include "ns3/packet.h"
#include "ns3/uinteger.h"
#include "ns3/trace-source-accessor.h"
#include "ns3/tcp-socket-factory.h"
#include "ns3/tcp-socket-base.h"
#include "ns3/tcp-tx-buffer.h"
#include "ns3/exp-util.h"
#include "tcp-paced-flow-send-application.h"
#include <fstream>
#include <utility>

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("TcpPacedFlowSendApplication");

NS_OBJECT_ENSURE_REGISTERED (TcpPacedFlowSendApplication);

TypeId
TcpPacedFlowSendApplication::GetTypeId(void) {
    static TypeId tid = TypeId("ns3::TcpPacedFlowSendApplication")
            .SetParent<TcpFlowSendApplication>()
            .SetGroupName("Applications")
            .AddConstructor<TcpPacedFlowSendApplication>()
            .AddAttribute ("PacingDataRate",
                           "Limit the Data Rate of the application",
                           DataRateValue (DataRate("1000000GB/s")),
                           MakeDataRateAccessor (&TcpPacedFlowSendApplication::m_bps),
                           MakeDataRateChecker ());
    return tid;
}


TcpPacedFlowSendApplication::TcpPacedFlowSendApplication()
        : TcpFlowSendApplication(),
          m_pacing(false), 
          m_sending_ongoing(true) {
    NS_LOG_FUNCTION(this);
    Packet::EnablePrinting();
}

TcpPacedFlowSendApplication::~TcpPacedFlowSendApplication() {
    NS_LOG_FUNCTION(this);
}

void TcpPacedFlowSendApplication::StopApplication(void) { // Called at time specified by Stop
    NS_LOG_FUNCTION(this);
    if (m_socket != 0) {
        m_socket->Close();
        m_connected = false;
        //m_endPacingEvent.Cancel();
    } else {
        NS_LOG_WARN("TcpPacedFlowSendApplication found null socket to close in StopApplication");
    }
}

void TcpPacedFlowSendApplication::EndPacing(){
    NS_LOG_FUNCTION(this);
    m_pacing=false;
    if (m_sending_ongoing){
        SendData();
    }
}
void TcpPacedFlowSendApplication::SendData(void) {
    NS_LOG_FUNCTION(this);
    if (m_pacing){
            m_sending_ongoing=true;
    } else if (m_maxBytes == 0 || m_totBytes < m_maxBytes) { // Time to send more
        
        // uint64_t to allow the comparison later.
        // the result is in a uint32_t range anyway, because
        // m_sendSize is uint32_t.
        uint64_t toSend = m_sendSize;
        // Make sure we don't send too many
        if (m_maxBytes > 0) {
            toSend = std::min(toSend, m_maxBytes - m_totBytes);
        }

        NS_LOG_LOGIC("sending packet at " << Simulator::Now());
        Ptr <Packet> packet = Create<Packet>(toSend);
        int actual = m_socket->Send(packet);
        if (actual > 0) {
            m_totBytes += actual;
            m_txTrace(packet);

            m_endPacingEvent = Simulator::Schedule(NanoSeconds(static_cast<uint64_t>(static_cast<double>(actual)*8e9/m_bps.GetBitRate())), &TcpPacedFlowSendApplication::EndPacing, this);
            NS_LOG_LOGIC("attente " << actual*8e3/m_bps.GetBitRate() << "ms fId" << m_tcpFlowId );
            m_pacing=true;
        }
        // We exit this loop when actual < toSend as the send side
        // buffer is full. The "DataSent" callback will pop when
        // some buffer space has freed up.
        if ((unsigned) actual != toSend) {
            m_sending_ongoing=false;
        }
    }
    // Check if time to close (all sent)
    if (m_totBytes == m_maxBytes && m_connected) {
        m_socket->Close(); // Close will only happen after send buffer is finished
        m_connected = false;
        m_endPacingEvent.Cancel();
    }
}
/*
void TcpPacedFlowSendApplication::DataSend(Ptr <Socket>, uint32_t) {
    NS_LOG_FUNCTION(this);
    if (m_connected) { // Only send new data if the connection has completed
        SendData();
    }

    // Log the progress as DataSend() is called anytime space in the transmission buffer frees up
    if (m_enableDetailedLogging) {
        InsertProgressLog(
                Simulator::Now ().GetNanoSeconds (),
                GetAckedBytes()
        );
    }

}*/

} // Namespace ns3
