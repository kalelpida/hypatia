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
#include "ns3/integer.h"
#include "ns3/string.h"
#include "ns3/pointer.h"


namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("ExtraChannelErrorModels"); // cannot merge it with ErrorModel component

//
// GilbEllErrorModel
//
NS_OBJECT_ENSURE_REGISTERED (GilbEllErrorModel);

TypeId GilbEllErrorModel::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::GilbEllErrorModel")
    .SetParent<ErrorModel> ()
    .SetGroupName("Network")
    .AddConstructor<GilbEllErrorModel> ()
    .AddAttribute ("ErrorRate", "The burst error event.",
                   DoubleValue (0.0),
                   MakeDoubleAccessor (&GilbEllErrorModel::m_burstRate),
                   MakeDoubleChecker<double> ())
    .AddAttribute ("BurstStart", "The decision variable attached to this error model.",
                   StringValue ("ns3::UniformRandomVariable[Min=0.0|Max=1.0]"),
                   MakePointerAccessor (&GilbEllErrorModel::m_burstStart),
                   MakePointerChecker<RandomVariableStream> ())
    .AddAttribute ("BurstSize", "The number of packets being corrupted at one drop.",
                   StringValue ("ns3::WeibullRandomVariable[Scale=4]"), //the integer part of an Exponential Random variable is geometric
                   MakePointerAccessor (&GilbEllErrorModel::m_burstSize),
                   MakePointerChecker<RandomVariableStream> ())
  ;
  return tid;
}

GilbEllErrorModel::GilbEllErrorModel () : m_currentBurstSz (0)
{

}

GilbEllErrorModel::~GilbEllErrorModel ()
{
  NS_LOG_FUNCTION (this);
}

double
GilbEllErrorModel::GetBurstRate (void) const
{
  NS_LOG_FUNCTION (this);
  return m_burstRate;
}

void
GilbEllErrorModel::SetBurstRate (double rate)
{
  NS_LOG_FUNCTION (this << rate);
  m_burstRate = rate;
}

void
GilbEllErrorModel::SetRandomVariable (Ptr<RandomVariableStream> ranVar)
{
  NS_LOG_FUNCTION (this << ranVar);
  m_burstStart = ranVar;
}

void
GilbEllErrorModel::SetRandomBurstSize(Ptr<RandomVariableStream> burstSz)
{
  NS_LOG_FUNCTION (this << burstSz);
  m_burstSize = burstSz;
}

int64_t
GilbEllErrorModel::AssignStreams (int64_t stream)
{
  NS_LOG_FUNCTION (this << stream);
  m_burstStart->SetStream (stream);
  m_burstSize->SetStream(stream);
  return 2;
}

bool
GilbEllErrorModel::DoCorrupt (Ptr<Packet> p)
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
GilbEllErrorModel::DoReset (void)
{
  NS_LOG_FUNCTION (this);
  m_currentBurstSz = 0;

}

#ifndef STATES_ERROR_MODEL_H
//erreurs à corriger 
//
// PeriodicErrorModel
//
NS_OBJECT_ENSURE_REGISTERED (PeriodicErrorModel);

TypeId PeriodicErrorModel::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::PeriodicErrorModel")
    .SetParent<ErrorModel> ()
    .SetGroupName("Network")
    .AddConstructor<PeriodicErrorModel> ()
    .AddAttribute ("ErrorRate", "The error event rate.",
                   DoubleValue (0.0),
                   MakeDoubleAccessor (&PeriodicErrorModel::m_faultyPeriodRate),
                   MakeDoubleChecker<double> ())
    .AddAttribute ("Period", "The period of the model.",
                   IntegerValue (60000000000), //1min
                   MakeIntegerAccessor (&PeriodicErrorModel::m_rotationPeriod_ns),
                   MakeIntegerChecker<RandomVariableStream> ())
    .AddAttribute ("DriftModel", "The number of packets being corrupted at one drop.",
                   StringValue ("ns3::NormalRandomVariable[mean=0, variance=0.1]"),
                   MakePointerAccessor (&PeriodicErrorModel::m_ranRotationVelocity_msps),
                   MakePointerChecker<RandomVariableStream> ())
  ;
  return tid;
}

PeriodicErrorModel::PeriodicErrorModel () : m_lastTime_ns (0)
{

}

PeriodicErrorModel::~PeriodicErrorModel ()
{
  NS_LOG_FUNCTION (this);
}

double
PeriodicErrorModel::GetErrorRate (void) const
{
  NS_LOG_FUNCTION (this);
  return m_faultyPeriodRate;
}

void
PeriodicErrorModel::SetErrorRate (double rate)
{
  NS_LOG_FUNCTION (this << rate);
  m_faultyPeriodRate = rate;
}

void
PeriodicErrorModel::SetRotationPeriod (int64_t period)
{
  NS_LOG_FUNCTION (this << period);
  m_rotationPeriod_ns = period;
}
int64_t
PeriodicErrorModel::GetRotationPeriod (void) const
{
  NS_LOG_FUNCTION (this);
  return m_rotationPeriod_ns;
}

void
PeriodicErrorModel::SetRandomVariable (Ptr<RandomVariableStream> ranVar)
{
  NS_LOG_FUNCTION (this << ranVar);
  m_ranRotationVelocity_msps = ranVar;
}

int64_t
PeriodicErrorModel::AssignStreams (int64_t stream)
{
  NS_LOG_FUNCTION (this << stream);
  m_ranRotationVelocity_msps->SetStream (stream);
  return 2;
}

bool
PeriodicErrorModel::DoCorrupt (Ptr<Packet> p)
{
  NS_LOG_FUNCTION (this);

  if (!IsEnabled ())
    {
      return false;
    }
  //int64_t m_lastTime_ns;                               //!< dernier temps de mise à jour de la vitesse de rotation       
  //double m_faultyPeriodRate;                     //!< the burst error event
  int64_t now_ns = Simulator::Now().GetNanoSeconds();
  bool resultat;
  
  if (static_cast<double>(now_ns%m_rotationPeriod_ns)/static_cast<double>(m_rotationPeriod_ns) < m_faultyPeriodRate)
    {
      // packet loss
      resultat=true;
    } 
  else 
    {
      resultat=false;
    }

  // update rotation period
  int64_t periodUpdate = static_cast<int64_t>(m_ranRotationVelocity_msps->GetValue()*(now_ns-m_lastTime_ns)*1e-6);
  m_rotationPeriod_ns = (m_rotationPeriod_ns > - periodUpdate) ?  m_rotationPeriod_ns+periodUpdate : 1;//period cannot be smaller than 1ns
  m_lastTime_ns = now_ns;

  return resultat;
}

void
PeriodicErrorModel::DoReset (void)
{
  NS_LOG_FUNCTION (this);
  m_lastTime_ns = 0;

}
#endif
}