#ifndef TRACE_JOURNAL_H
#define TRACE_JOURNAL_H
#include <map>
#include "ns3/ipv4.h"
#include "ns3/id-seq-header.h"
#include "ns3/output-stream-wrapper.h"
#include "ns3/nstime.h"
//#include "ns3/internet-module.h"

namespace ns3 {

    struct structacceptNodeObj { 
        unsigned int minNodeId; 
    };

    typedef std::map<std::pair<InetSocketAddress,Ipv4Address>, uint64_t> mapflow_t;
    typedef struct structacceptNodeObj acceptNodeObj;

    struct structCbParams{
        mapflow_t *m_conversion;
        acceptNodeObj m_log_condition_NodeId;
    };
    
    typedef struct structCbParams cbparams;

    void PacketEventTracer(Ptr<OutputStreamWrapper> stream,  cbparams* cbparams_val, const std::string& infodrop, Ptr<const Node> src_node, Ptr<const Node> dst_node,  Ptr<const Packet> packet, const Time& txTime);
    void PacketEventTracerSimple(Ptr<OutputStreamWrapper> stream, cbparams* cbparams_val, const std::string& infodrop, Ptr<const Node> node, Ptr<const Packet> packet, const Time& rxTime);
    void PacketEventTracerReduit(Ptr<OutputStreamWrapper> stream, cbparams* cbparams_val, const std::string& infodrop, Ptr<const Node> node, Ptr<const Packet> packet);

}   
#endif