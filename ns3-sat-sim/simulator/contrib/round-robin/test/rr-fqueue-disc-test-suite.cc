/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2017 Universita' degli Studi di Napoli Federico II
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
 * Authors: Stefano Avallone <stavallo@unina.it>
 *          Paul
 *
 */

#include "ns3/test.h"
#include "ns3/rr-fqueue-disc.h"
#include "ns3/queue.h"
#include "ns3/packet.h"
#include "ns3/uinteger.h"
#include "ns3/string.h"
#include "ns3/double.h"
#include "ns3/log.h"
#include "ns3/simulator.h"
#include "ns3/object-factory.h"
#include "ns3/ipv4-header.h"
#include "ns3/ipv4-queue-disc-item.h"
#include <vector>

using namespace ns3;

/**
 * \ingroup traffic-control-test
 * \ingroup tests
 *
 * \brief Fifo Queue Disc Test Item
 */
class RRFQueueDiscTestItem : public QueueDiscItem
{
public:
  /**
   * Constructor
   *
   * \param p the packet
   * \param addr the address
   */
  RRFQueueDiscTestItem (Ptr<Packet> p, const Address & addr);
  virtual ~RRFQueueDiscTestItem ();
  virtual void AddHeader (void);
  virtual bool Mark (void);

private:
  RRFQueueDiscTestItem ();
  /**
   * \brief Copy constructor
   * Disable default implementation to avoid misuse
   */
  RRFQueueDiscTestItem (const RRFQueueDiscTestItem &);
  /**
   * \brief Assignment operator
   * \return this object
   * Disable default implementation to avoid misuse
   */
  RRFQueueDiscTestItem &operator = (const RRFQueueDiscTestItem &);
};

RRFQueueDiscTestItem::RRFQueueDiscTestItem (Ptr<Packet> p, const Address & addr)
  : QueueDiscItem (p, addr, 0)
{
}

RRFQueueDiscTestItem::~RRFQueueDiscTestItem ()
{
}

void
RRFQueueDiscTestItem::AddHeader (void)
{
}

bool
RRFQueueDiscTestItem::Mark (void)
{
  return false;
}


static 
Ptr<Ipv4QueueDiscItem> createIpv4Qitem(uint32_t pktSize, const char* dst_addr){
  Ipv4Header h;
  h.SetDestination(Ipv4Address(dst_addr));
  Ptr<Packet> p = Create<Packet>(pktSize-h.GetSerializedSize());
  Ptr<Ipv4QueueDiscItem> qIt=Create<Ipv4QueueDiscItem>(p, Address(), 0, h);
  return qIt;
}



/**
 * \ingroup traffic-control-test
 * \ingroup tests
 *
 * \brief Fifo Queue Disc Test Case
 */
class RRFQueueDiscTestCase : public TestCase
{
public:
  RRFQueueDiscTestCase ();
  virtual void DoRun (void);
private:
  /**
   * Run test function
   * \param mode the test mode
   */
  void RunRRFQueueTest (QueueSizeUnit mode);
  /**
   * Run test function
   * \param q the queue disc
   * \param qSize the expected size of the queue disc
   * \param pktSize the packet size
   */
  void DoRunRRFQueueTestOneDest(Ptr<RRFQueueDisc> q, uint32_t qSize, uint32_t pktSize);
  void DoRunRRFQueueSimpleTest (Ptr<RRFQueueDisc> q, uint32_t qSize, uint32_t pktSize, uint32_t n_dests);
};

RRFQueueDiscTestCase::RRFQueueDiscTestCase ()
  : TestCase ("Sanity check on the fifo queue disc implementation")
{
}

static 
Ptr<Packet> createSrcIpv4Packet(uint32_t pktSize, const char* src_addr){
  Ptr<Packet> p=Create<Packet>();
  Ipv4Header h;
  h.SetSource(Ipv4Address(src_addr));
  p->AddHeader(h);
  return p;
}

void
RRFQueueDiscTestCase::DoRunRRFQueueTestOneDest (Ptr<RRFQueueDisc> q, uint32_t qSize, uint32_t pktSize)
{
  std::vector<uint64_t> uids;
  Ptr<Ipv4QueueDiscItem> qIt;
  Ptr<QueueDiscItem> item;
  Address dest;
  uint32_t modeSize = (q->GetMaxSize ().GetUnit () == QueueSizeUnit::PACKETS ? 1 : pktSize);
  uint32_t numPackets = qSize / modeSize;

  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 0, "The queue disc should be empty");

  // create and enqueue numPackets packets and store their UIDs; check they are all enqueued
  for (uint32_t i = 1; i <= numPackets; i++)
    {
      qIt = createIpv4Qitem(pktSize, "10.0.0.1");
      uids.push_back (qIt->GetPacket()->GetUid ());
      q->Enqueue (qIt);
      NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), i * modeSize, "There should be " << i << " packet(s) in there");
    }

  // no room for another packet
  NS_TEST_EXPECT_MSG_EQ (q->Enqueue (createIpv4Qitem(pktSize, "10.0.0.1")),
                         false, "There should be no room for another packet");

  // dequeue and check packet order
  for (uint32_t i = 1; i <= numPackets; i++)
    {
      item = q->Dequeue ();
      
      NS_ASSERT_MSG (!item == false, "A packet should have been dequeued");
      NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), (numPackets-i) * modeSize, "There should be " << numPackets-i << " packet(s) in there");
      NS_TEST_EXPECT_MSG_EQ (item->GetPacket ()->GetUid (), uids[i-1], "was this the right packet?");
    }

  item = q->Dequeue ();
  NS_ASSERT_MSG ((item == 0), "There are really no packets in there");
}


void
RRFQueueDiscTestCase::DoRunRRFQueueSimpleTest (Ptr<RRFQueueDisc> q, uint32_t qSize, uint32_t pktSize, uint32_t n_dests)
{
  /*
  Queues representation. * represent the length of a packet
  1  *| ***| **
  2  **| *| ***
  3  *****  |  *|
  */
  std::vector<uint64_t> uids;
  Ptr<Ipv4QueueDiscItem> qIt;
  Ptr<QueueDiscItem> item;
  Address dest;
  uint32_t expectedNumPackets;
  NS_ASSERT_MSG(q->GetMaxSize ().GetUnit ()== QueueSizeUnit::BYTES, "This test only works for byte queue size counters");
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 0, "The queue disc should be empty");
  NS_ASSERT_MSG((n_dests>0) && (n_dests <= 256), "bad number of destinations");
  q->Clean();


  qIt = createIpv4Qitem(pktSize, "10.0.0.1");
  uids.push_back (qIt->GetPacket()->GetUid ());
  q->Enqueue (qIt);
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), pktSize, "There should be " << 1 << " packet(s) in there"); 
  
  qIt = createIpv4Qitem(2*pktSize, "10.0.0.2");
  uids.push_back (qIt->GetPacket()->GetUid ());
  q->Enqueue (qIt);
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 3*pktSize, "There should be " << 2 << " packet(s) in there");

  qIt = createIpv4Qitem(5*pktSize, "10.0.0.3");
  uids.push_back (qIt->GetPacket()->GetUid ());
  q->Enqueue (qIt);
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 8*pktSize, "There should be " << 3 << " packet(s) in there");

  qIt = createIpv4Qitem(3*pktSize, "10.0.0.1");
  uids.push_back (qIt->GetPacket()->GetUid ());
  q->Enqueue (qIt);
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 11*pktSize, "There should be " << 4 << " packet(s) in there"); 
  
  qIt = createIpv4Qitem(1*pktSize, "10.0.0.2");
  uids.push_back (qIt->GetPacket()->GetUid ());
  q->Enqueue (qIt);
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 12*pktSize, "There should be " << 5 << " packet(s) in there");
  
  qIt = createIpv4Qitem(3*pktSize, "10.0.0.2");
  uids.push_back (qIt->GetPacket()->GetUid ());
  q->Enqueue (qIt);
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 15*pktSize, "There should be " << 6 << " packet(s) in there");

  qIt = createIpv4Qitem(2*pktSize, "10.0.0.1");
  uids.push_back (qIt->GetPacket()->GetUid ());
  q->Enqueue (qIt);
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 17*pktSize, "There should be " << 7 << " packet(s) in there"); 

  qIt = createIpv4Qitem(pktSize, "10.0.0.3");
  uids.push_back (qIt->GetPacket()->GetUid ());
  q->Enqueue (qIt);
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 18*pktSize, "There should be " << 8 << " packet(s) in there");
  // no room for another packet
  //TODO
  /*
  for(uint32_t dst = 0; dst<n_dests; dst++){
      NS_TEST_EXPECT_MSG_EQ (q->Enqueue (createIpv4Qitem(pktSize, ("10.0.0."+std::to_string(dst)).c_str())),
                         false, "There should be no room for another packet"); 
      }
  */

  // dequeue and check packet order
  item = q->Dequeue ();
  
  NS_ASSERT_MSG (!item == false, "A packet should have been dequeued");
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 17*pktSize, "There should be " << 7 << " packet(s) in there, real size " << q->GetCurrentSize ().GetValue ());
  NS_TEST_EXPECT_MSG_EQ (item->GetPacket ()->GetUid (), uids[0], "was this the right packet?");

  item = q->Dequeue ();
  
  NS_ASSERT_MSG (!item == false, "A packet should have been dequeued");
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 15*pktSize, "There should be " << 6 << " packet(s) in there, real size " << q->GetCurrentSize ().GetValue ());
  NS_TEST_EXPECT_MSG_EQ (item->GetPacket ()->GetUid (), uids[1], "was this the right packet?");

  item = q->Dequeue ();
  
  NS_ASSERT_MSG (!item == false, "A packet should have been dequeued");
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 10*pktSize, "There should be " << 5 << " packet(s) in there, real size " << q->GetCurrentSize ().GetValue ());
  NS_TEST_EXPECT_MSG_EQ (item->GetPacket ()->GetUid (), uids[2], "was this the right packet?");

  item = q->Dequeue ();
  
  NS_ASSERT_MSG (!item == false, "A packet should have been dequeued");
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 7*pktSize, "There should be " << 4 << " packet(s) in there, real size " << q->GetCurrentSize ().GetValue ());
  NS_TEST_EXPECT_MSG_EQ (item->GetPacket ()->GetUid (), uids[3], "was this the right packet?");

  item = q->Dequeue ();
  
  NS_ASSERT_MSG (!item == false, "A packet should have been dequeued");
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 6*pktSize, "There should be " << 3 << " packet(s) in there, real size " << q->GetCurrentSize ().GetValue ());
  NS_TEST_EXPECT_MSG_EQ (item->GetPacket ()->GetUid (), uids[4], "was this the right packet?");

  item = q->Dequeue ();
  
  NS_ASSERT_MSG (!item == false, "A packet should have been dequeued");
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 3*pktSize, "There should be " << 2 << " packet(s) in there, real size " << q->GetCurrentSize ().GetValue ());
  NS_TEST_EXPECT_MSG_EQ (item->GetPacket ()->GetUid (), uids[5], "was this the right packet?");

  item = q->Dequeue ();
  
  NS_ASSERT_MSG (!item == false, "A packet should have been dequeued");
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 1*pktSize, "There should be " << 1 << " packet(s) in there, real size " << q->GetCurrentSize ().GetValue ());
  NS_TEST_EXPECT_MSG_EQ (item->GetPacket ()->GetUid (), uids[6], "was this the right packet?");

  item = q->Dequeue ();
  
  NS_ASSERT_MSG (!item == false, "A packet should have been dequeued");
  NS_TEST_EXPECT_MSG_EQ (q->GetCurrentSize ().GetValue (), 0, "There should be " << 0 << " packet(s) in there, real size " << q->GetCurrentSize ().GetValue ());
  NS_TEST_EXPECT_MSG_EQ (item->GetPacket ()->GetUid (), uids[7], "was this the right packet?");


  item = q->Dequeue ();
  NS_TEST_EXPECT_MSG_EQ (item, 0, "There are really no packets in there");
}

void
RRFQueueDiscTestCase::RunRRFQueueTest (QueueSizeUnit mode)
{
  Ptr<RRFQueueDisc> queue;
  uint32_t numPackets = 18;
  uint32_t pktSize = 1000;
  uint32_t modeSize = (mode == QueueSizeUnit::PACKETS ? 1 : pktSize);

  // test 1: set the limit on the queue disc before initialization
  queue = CreateObject<RRFQueueDisc> ();

  NS_TEST_EXPECT_MSG_EQ (queue->GetNInternalQueues(), 0, "Verify that the queue disc has no internal queue");

  NS_TEST_EXPECT_MSG_EQ (queue->SetAttributeFailSafe ("MaxSize",
                                                      QueueSizeValue (QueueSize (mode, numPackets*modeSize))), true,
                     "Verify that we can actually set the attribute MaxSize");

  queue->Initialize ();

  DoRunRRFQueueTestOneDest (queue, numPackets*modeSize, pktSize);
  if (mode==QueueSizeUnit::BYTES){
    DoRunRRFQueueSimpleTest (queue, numPackets*modeSize, pktSize, 10);
  }

  // test 2: set the limit on the queue disc after initialization
  //will fail, will not change size of different queues
  /*
  queue = CreateObject<RRFQueueDisc> ();

  NS_ASSERT_MSG (queue->GetNInternalQueues ()== 0, "Verify that the queue disc has no internal queue");

  queue->Initialize ();

  NS_ASSERT_MSG (queue->SetAttributeFailSafe ("MaxSize",
                                                      QueueSizeValue (QueueSize (mode, numPackets*modeSize))),
                         "Verify that we can actually set the attribute MaxSize");

  RRFQueueTest (queue, numPackets*modeSize, pktSize);*/

}
void
RRFQueueDiscTestCase::DoRun (void){
  /*//for debug
  std::string attente;
  std::cout << "attente ";
  std::cin >> attente;
  */
  RunRRFQueueTest (QueueSizeUnit::PACKETS);//not so useful
  RunRRFQueueTest (QueueSizeUnit::BYTES);
  Simulator::Destroy ();
}



/**
 * \ingroup traffic-control-test
 * \ingroup tests
 *
 * \brief Fifo Queue Disc Test Suite
 */
static class RRFQueueDiscTestSuite : public TestSuite
{
public:
  RRFQueueDiscTestSuite ()
    : TestSuite ("round-robin", UNIT)
  {
    AddTestCase (new RRFQueueDiscTestCase (), TestCase::QUICK);
  }
} g_RRFQueueTestSuite; ///< the test suite
