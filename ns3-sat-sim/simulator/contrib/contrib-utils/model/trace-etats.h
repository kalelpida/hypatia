#ifndef TRACE_ETATS_H
#define TRACE_ETATS_H
#include <map>
#include "ns3/queue.h"
#include "ns3/simulator.h"
#include "ns3/net-device.h"
#include "ns3/output-stream-wrapper.h"
#include "ns3/queue-disc.h"
#include "ns3/data-rate.h"


namespace ns3 {

    struct structLoopParams{
        uint32_t nodeId;
        std::string specie;
        uint32_t ifnum;
        std::string infoIf;
        Ptr<Queue<Packet>> queue;
        Time delai_capture;
        DataRate debit;
    };

    struct structLoopParamsBis{
        uint32_t nodeId;
        std::string specie;
        uint32_t ifnum;
        std::string infoIf;
        Ptr<QueueDisc> qd;
        const QueueDisc::Stats qd_stats;
        Time delai_capture;
        DataRate debit;
    };
    
    typedef struct structLoopParams pktQloparams;
    typedef struct structLoopParamsBis qDiscloparams;

    void PktQloopingStats(Ptr<OutputStreamWrapper> stream, const pktQloparams& loparams_val);
    void QDiscloopingStats(Ptr<OutputStreamWrapper> stream, const qDiscloparams loparams_val);
    void setupQlog(Ptr<OutputStreamWrapper> stream, Ptr<Node> node, Ptr<NetDevice> base_ndev, TypeId tid, Time time_interval, const std::string& link);

}   
#endif