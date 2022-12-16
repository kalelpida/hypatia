/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2007 University of Washington
 * Copyright (c) 2013 ResiliNets, ITTC, University of Kansas 
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
 *
 * This file incorporates work covered by the following copyright and  
 * permission notice:   
 *
 * Copyright (c) 1997 Regents of the University of California.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the University nor of the Laboratory may be used
 *    to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 * Contributed by the Daedalus Research Group, UC Berkeley
 * (http://daedalus.cs.berkeley.edu)
 *
 */

/* 
 * Since I was not able to characterize the BurstErrorModel behaviour (why would I whip myself with stochastic processes ?), 
 * I decided to rewrite it with another version of the DoCorrupt method. 
 * The complexity is reported in the choice of the burst length distribution.
 */



#include <cmath>

#include "states-error-model.h"

#include "ns3/packet.h"
#include "ns3/assert.h"
#include "ns3/log.h"
#include "ns3/boolean.h"
#include "ns3/enum.h"
#include "ns3/double.h"
#include "ns3/string.h"
#include "ns3/pointer.h"


namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("StatesErrorModel"); // cannot merge it with ErrorModel component

//
// StatesErrorModel
//
NS_OBJECT_ENSURE_REGISTERED (StatesErrorModel);

TypeId StatesErrorModel::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::StatesErrorModel")
    .SetParent<ErrorModel> ()
    .SetGroupName("Network")
    .AddConstructor<StatesErrorModel> ()
    .AddAttribute ("ErrorRate", "The burst error event.",
                   DoubleValue (0.0),
                   MakeDoubleAccessor (&StatesErrorModel::m_burstRate),
                   MakeDoubleChecker<double> ())
    .AddAttribute ("BurstStart", "The decision variable attached to this error model.",
                   StringValue ("ns3::UniformRandomVariable[Min=0.0|Max=1.0]"),
                   MakePointerAccessor (&StatesErrorModel::m_burstStart),
                   MakePointerChecker<RandomVariableStream> ())
    .AddAttribute ("BurstSize", "The number of packets being corrupted at one drop.",
                   StringValue ("ns3::WeibullRandomVariable[Scale=4]"), //the integer part of an Exponential Random variable is geometric
                   MakePointerAccessor (&StatesErrorModel::m_burstSize),
                   MakePointerChecker<RandomVariableStream> ())
  ;
  return tid;
}

StatesErrorModel::StatesErrorModel () : m_currentBurstSz (0)
{

}

StatesErrorModel::~StatesErrorModel ()
{
  NS_LOG_FUNCTION (this);
}

double
StatesErrorModel::GetBurstRate (void) const
{
  NS_LOG_FUNCTION (this);
  return m_burstRate;
}

void
StatesErrorModel::SetBurstRate (double rate)
{
  NS_LOG_FUNCTION (this << rate);
  m_burstRate = rate;
}

void
StatesErrorModel::SetRandomVariable (Ptr<RandomVariableStream> ranVar)
{
  NS_LOG_FUNCTION (this << ranVar);
  m_burstStart = ranVar;
}

void
StatesErrorModel::SetRandomBurstSize(Ptr<RandomVariableStream> burstSz)
{
  NS_LOG_FUNCTION (this << burstSz);
  m_burstSize = burstSz;
}

int64_t
StatesErrorModel::AssignStreams (int64_t stream)
{
  NS_LOG_FUNCTION (this << stream);
  m_burstStart->SetStream (stream);
  m_burstSize->SetStream(stream);
  return 2;
}

bool
StatesErrorModel::DoCorrupt (Ptr<Packet> p)
{
  NS_LOG_FUNCTION (this);
  if (!IsEnabled ())
    {
      return false;
    }
  
  if (m_currentBurstSz == 0)
    {
      // just get in Good mode, so no packet loss
      m_currentBurstSz--;
      return false;
    } 
  else if (m_currentBurstSz > 0)
    {
      // still in burst mode
      m_currentBurstSz--;
      return true;    // drop this packet
    }
  else
    {
      double ranVar = m_burstStart ->GetValue();
      if (ranVar < m_burstRate)
        {
          // create a new burst
          m_currentBurstSz = static_cast<int32_t>(m_burstSize->GetInteger()); 
          // get a new burst size for the new error event   
          return true;    // drop this packet
        }
      else
        {
          // all packets in the last error event have been dropped
          // and there is no new error event, so do not drop the packet
          return false;  // no error event
        }
    }
}

void
StatesErrorModel::DoReset (void)
{
  NS_LOG_FUNCTION (this);
  m_currentBurstSz = 0;

}
}