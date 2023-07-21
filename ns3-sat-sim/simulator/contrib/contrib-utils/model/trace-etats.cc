#include "trace-etats.h"
#include "ns3/specie.h"
#include "ns3/traffic-control-layer.h"
#include "ns3/queue-disc.h"
#include <memory> 
#include "ns3/gsl-net-device.h"
#include "ns3/point-to-point-laser-net-device.h"
#include "ns3/point-to-point-tracen-net-device.h"

namespace ns3 {

void PktQloopingStats(Ptr<OutputStreamWrapper> stream, const pktQloparams& loparams_val){
    Ptr<Queue<Packet>> q=loparams_val.queue;
    if (q->GetTotalReceivedBytes()>0){// dont log queue which did not get any packet during interval
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << loparams_val.nodeId << ","  << loparams_val.specie << "," << loparams_val.ifnum << "," << loparams_val.infoIf << ",";
        if (q->GetMaxSize().GetUnit () == QueueSizeUnit::PACKETS){
            *stream->GetStream() << q->GetMaxSize().GetValue() << ",pkt," << q->GetNPackets();
        } else {
            *stream->GetStream() << q->GetMaxSize().GetValue() << ",oct," << q->GetNBytes(); 
        }
        *stream->GetStream() << "," << q->GetTotalReceivedBytes() << "," << q->GetTotalDroppedBytes() << std::endl;
        loparams_val.queue->ResetStatistics();
    }
    Simulator::Schedule(loparams_val.delai_capture, &PktQloopingStats, stream, loparams_val);
}

void QDiscloopingStats(Ptr<OutputStreamWrapper> stream, const qDiscloparams lprms){
    const QueueDisc::Stats qds=lprms.qd->GetStats();
    //std::cout << "::    nouvelles   ::";
    //qds.Print(std::cout);
    //std::cout << "::    ancienne    ::";
    //lprms.qd_stats.Print(std::cout);
    //std::cout << "\n\n" << std::endl;
    if (qds.nTotalReceivedBytes > lprms.qd_stats.nTotalReceivedBytes){// dont log queue which did not get any packet during interval
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << lprms.nodeId << ","  << lprms.specie << "," << lprms.ifnum << "," << lprms.infoIf << ",";
        if (lprms.qd->GetMaxSize().GetUnit () == QueueSizeUnit::PACKETS){
                *stream->GetStream() << lprms.qd->GetMaxSize().GetValue() << ",pkt," << lprms.qd->GetNPackets();
            } else {
                *stream->GetStream() << lprms.qd->GetMaxSize().GetValue() << ",oct," << lprms.qd->GetNBytes() ; 
            }
        *stream->GetStream() << "," << qds.nTotalReceivedBytes - lprms.qd_stats.nTotalReceivedBytes << "," << qds.nTotalDroppedBytes - lprms.qd_stats.nTotalDroppedBytes << std::endl;
    }
    Simulator::Schedule(lprms.delai_capture, &QDiscloopingStats, stream, qDiscloparams({lprms.nodeId, lprms.specie, lprms.ifnum, lprms.infoIf, lprms.qd, qds, lprms.delai_capture}));

}

//if (n1->GetId() > m_cbparams.m_log_condition_NodeId.minNodeId){
void setupQlog(Ptr<OutputStreamWrapper> stream, Ptr<Node> node, Ptr<NetDevice> base_ndev, TypeId tid, Time time_interval, const std::string& link){
    Ptr<Queue<Packet>> qp;
    if (TypeId::LookupByName("ns3::PointToPointTracenNetDevice")==tid){
        Ptr<PointToPointTracenNetDevice> netdev= base_ndev->GetObject<PointToPointTracenNetDevice>();//dynamic_cast<PointToPointTracenNetDevice*>(&*base_ndev);
        qp=netdev->GetQueue();
    } else if (TypeId::LookupByName("ns3::PointToPointLaserNetDevice")==tid){
        Ptr<PointToPointLaserNetDevice> netdev= base_ndev->GetObject<PointToPointLaserNetDevice>();
        qp=netdev->GetQueue();
    } else if (TypeId::LookupByName("ns3::GSLNetDevice")==tid){
        Ptr<GSLNetDevice> netdev= base_ndev->GetObject<GSLNetDevice>();
        qp=netdev->GetQueue();
    } else {
        NS_ABORT_MSG("Non recognised netdevice on node num" << node->GetId() << " specie "<< node->GetObject<Specie>()->GetName() << " interface " <<base_ndev->GetIfIndex());
    }
    PktQloopingStats(stream, {node->GetId(), node->GetObject<Specie>()->GetName(), base_ndev->GetIfIndex(), link, qp, time_interval });
    Ptr<TrafficControlLayer> tc = node->GetObject<TrafficControlLayer>();
    if (tc){
        Ptr<QueueDisc> qd = tc->GetRootQueueDiscOnDevice(base_ndev);
        if (qd){
            QDiscloopingStats(stream, qDiscloparams({node->GetId(), node->GetObject<Specie>()->GetName(), base_ndev->GetIfIndex(), link+"-tc", qd, qd->GetStats(), time_interval }));
        }
    }
}
}

/*
Please can someone help me understanding, Simulator::ScheduleWithContext function ? What is actually meant by the "context" thing ? Any related example will be very helpful.

Simulator::ScheduleWithContext 	( 	uint32_t  	context,
	const Time &  	time,
	EventImpl *  	event 
	) 	

it's a seldom used thing. You can think about it as a numerical "tag" you assign to the event. When the event is executed, you can ask the Scheduler what is the current context and ... well, do what you want.

As an example, in the function "Node::ReceiveFromDevice", there is the following line:
  NS_ASSERT_MSG (Simulator::GetContext () == GetId (), "Received packet with erroneous context ; " <<
                 "make sure the channels in use are correctly updating events context " <<
                 "when transferring events from one node to another.");

and indeed in the channel (let's use CsmaChannel as an example), you'll find this:
          // schedule reception events
          Simulator::ScheduleWithContext (it->devicePtr->GetNode ()->GetId (),
                                          m_delay,
                                          &CsmaNetDevice::Receive, it->devicePtr,
                                          m_currentPkt->Copy (), m_deviceList[m_currentSrc].devicePtr);


In this case the context is used to make sure that the event is really meant to be received by that node.


*/