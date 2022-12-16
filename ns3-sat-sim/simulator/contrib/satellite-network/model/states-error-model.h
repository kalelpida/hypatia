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
 * This code has been ported from ns-2 (queue/errmodel.{cc,h}
 */

/* BurstErrorModel additions
 *
 * Author: Truc Anh N. Nguyen   <annguyen@ittc.ku.edu>
 *         ResiliNets Research Group   http://wiki.ittc.ku.edu/resilinets
 *         James P.G. Sterbenz <jpgs@ittc.ku.edu>, director 
 */

#ifndef STATES_ERROR_MODEL_H
#define STATES_ERROR_MODEL_H

#include "ns3/error-model.h"

namespace ns3 {
/**
 * \brief Determine which bursts of packets are errored corresponding to 
 * an underlying distribution, burst rate, and burst size.
 * 
 * This is a rewriting of the BurstErrorModel, changing only the DoCorrupt Method
 * This one has two states, instead of the three in Burst Error Model
 * Unfortunately, it is created with provate parameters so this cannot derive directly 
 * from BurstErrorModel Class
 *
 * This object is used to flag packets as being lost/errored or not.
 * The two parameters that govern the behavior are the burst rate (or
 * equivalently, the mean duration/spacing between between error events), 
 * and the burst size (or equivalently, the number of packets being flagged 
 * as errored at each error event).
 *
 * Users can optionally provide RandomVariableStream objects;
 * the default for the decision variable is to use a Uniform(0,1) distribution;
 * the default for the burst size (number of packets) is to use a 
 * discrete Uniform[0,3] distribution.
 *
 * There are two states: Good and Bad.
 * When the state is good (burst size zero), the model checks for each packet 
 * if it should remain in Good state. 
 * When a burst is encountered, the model selects 
 * 
 *
 * IsCorrupt() will not modify the packet data buffer
 */

class StatesErrorModel: public ErrorModel
{
public:
  /**
   * \brief Get the type ID.
   * \return the object TypeId
   */
  static TypeId GetTypeId (void);

  StatesErrorModel ();
  virtual ~StatesErrorModel ();

  /**
   * \returns the error rate being applied by the model
   */
  double GetBurstRate (void) const;
  /**
   * \param rate the error rate to be used by the model
   */
  void SetBurstRate (double rate);

  /**
   * \param ranVar A random variable distribution to generate random variates
   */
  void SetRandomVariable (Ptr<RandomVariableStream> ranVar);

  /**
   * \param burstSz A random variable distribution to generate random burst size
   */
  void SetRandomBurstSize (Ptr<RandomVariableStream> burstSz);

  /**
    * Assign a fixed random variable stream number to the random variables
    * used by this model.  Return the number of streams (possibly zero) that
    * have been assigned.
    *
    * \param stream first stream index to use
    * \return the number of stream indices assigned by this model
    */
  int64_t AssignStreams (int64_t stream);

private:
  virtual bool DoCorrupt (Ptr<Packet> p);
  virtual void DoReset (void);

  double m_burstRate;                         //!< the burst error event
  Ptr<RandomVariableStream> m_burstStart;     //!< the error decision variable
  Ptr<RandomVariableStream> m_burstSize;      //!< the number of packets being flagged as errored

  int32_t m_currentBurstSz;                  //!< the current burst size
};

}

#endif