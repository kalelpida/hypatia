#include "trace-journal.h"
#include "ns3/specie.h"
#include "ns3/tcp-header.h"
#include "ns3/udp-header.h"
#include "ns3/ipv4-header.h"
#include "ns3/node.h"
#include "ns3/simulator.h"
#include "ns3/ipv4-queue-disc-item.h"
#include "ns3/tcp-option-ts.h"

namespace ns3 {

struct structresAnalysePacket{
    bool succes;
    bool isTCP;
    bool isReverse; // wether it comes from the destination
    uint32_t dataOffset;//corresponds to the fragment initial data, (o)
    uint32_t dataSize; 
    uint64_t idcomm;  
    uint64_t idseq; //used in UDP, corresponds to the offset of the data sent, in packets   
    uint32_t timestamp;//TCP option timestamp
    };

typedef struct structresAnalysePacket resAnalysePacket;

static void getPacketFlux(Ptr<const Packet> p, mapflow_t *conversion, resAnalysePacket& analysePacket){
        // Extract burst identifier and packet sequence number if UDP
        // Otherwise get flow identifier from packet sequence number
        static TypeId tidInteret= IdSeqHeader::GetTypeId();
        static TypeId tidtcpheader = TcpHeader::GetTypeId();
        static TypeId tidipheader = Ipv4Header::GetTypeId();
        static TypeId tidudpheader = UdpHeader::GetTypeId();

        auto it = p->BeginItem ();
        Ipv4Header ipheader;
        InetSocketAddress idSource((uint16_t)0);
        InetSocketAddress idDest((uint16_t)0);


        PacketMetadata::Item item;
        while (it.HasNext ()){
        item = it.Next ();
        if (item.tid == tidipheader){
            ipheader.Deserialize(item.current);
            idSource.SetIpv4(ipheader.GetSource());
            idDest.SetIpv4(ipheader.GetDestination());
            break;
        }
        }
        if (! it.HasNext()){
            p->Print(std::cerr);
            NS_ABORT_MSG("incomplete packet");
            return;
        }
        item = it.Next ();
        if (item.tid == tidudpheader){
            // that's UDP
            /*
            UdpHeader udpheader;
            udpheader.Deserialize(item.current);
            std::get<1>(idSource) = udpheader.GetSourcePort();
            std::get<1>(idDest) = udpheader.GetDestinationPort();
            const auto& conversionref = conversion;
            */
            
            if (! it.HasNext()){
                p->Print(std::cerr);
                NS_ABORT_MSG("incomplete packet");
            }
            item = it.Next ();
            if (item.tid!=tidInteret) {
                analysePacket.succes=false;//inintéressant, sans doute du ping
                return;
                //p->Print(std::cerr);
                //NS_ABORT_MSG("Not an usual Hypatia packet");
            }
            IdSeqHeader incomingIdSeq;
            incomingIdSeq.Deserialize(item.current);
            analysePacket.dataSize = item.currentSize;
            analysePacket.idcomm = incomingIdSeq.GetId();
            analysePacket.idseq = incomingIdSeq.GetSeq();
            
            // get into payload
            item = it.Next();
            NS_ASSERT_MSG(item.type == PacketMetadata::Item::ItemType::PAYLOAD, "not an usual Hypatia UDP packet");
            analysePacket.dataSize += item.currentSize;
            return;
        
        } else if (item.tid == tidtcpheader){
            TcpHeader tcpheader;
            analysePacket.isTCP = true;
            tcpheader.Deserialize(item.current);
            idSource.SetPort(tcpheader.GetSourcePort());
            idDest.SetPort(tcpheader.GetDestinationPort());

            // update commodity number
            const mapflow_t conversionref = *conversion;
            bool trouve=false;
            auto triplet = std::make_pair(idSource, idDest.GetIpv4());
            auto triplet_reverse = std::make_pair(idDest, idSource.GetIpv4());
            for (auto paire : conversionref){
                if (paire.first == triplet){
                    analysePacket.idcomm = paire.second;
                    trouve=true;
                    break;
                } else if (paire.first == triplet_reverse){
                    analysePacket.idcomm = paire.second;
                    analysePacket.isReverse = true;
                    trouve=true;
                    break;
                }
            }
            
            if (!trouve){
                std::cout << "New packet received:" << std::endl;
                p->Print(std::cout);
                std::cout << "\n Until now, only below commodities are listed" << std::endl;

                for (auto paire : conversionref){
                    std::cout << "src" << paire.first.first.GetIpv4() << ":" << paire.first.first.GetPort() << " ; dst " << paire.first.second << " ; related commodity: " << paire.second << std::endl;
                }
                NS_ABORT_MSG("Not recognised TCP packet:");
            }
            
            
            // update data info carried by the packet
            if (it.HasNext()){
                item = it.Next();
                NS_ASSERT_MSG(item.type == PacketMetadata::Item::ItemType::PAYLOAD, "not an usual Hypatia UDP packet");
                analysePacket.dataOffset = item.currentTrimedFromStart;
                analysePacket.dataSize = item.currentSize;
            } else {
                analysePacket.dataSize = 0;
            }
            while (it.HasNext()){
                item = it.Next();
                if (item.type == PacketMetadata::Item::ItemType::PAYLOAD){
                    analysePacket.dataSize += item.currentSize;
                }
            }
            
        } else {
            p->Print(std::cerr);
            NS_ABORT_MSG("Not an usual Hypatia packet");
        }
    }

void PacketEventTracer(Ptr<OutputStreamWrapper> stream,  cbparams* cbparams_val, const std::string& infodrop, Ptr<const Node> src_node, Ptr<const Node> dst_node,  Ptr<const Packet> packet, const Time& txTime)
{
    //NS_LOG_UNCOND("RxDrop at " << Simulator::Now().GetSeconds());
    if (cbparams_val->m_log_condition_NodeId.minNodeId <= std::max(src_node->GetId(), dst_node->GetId())){
    resAnalysePacket analysePacket = {true, false, false, 0, 0, 0, 0, 0};
    getPacketFlux(packet, cbparams_val->m_conversion, analysePacket);
    // Log precise timestamp received of the sequence packet if needed
    if (analysePacket.succes){
    *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << packet->GetUid() << "," << src_node->GetId() << "," << src_node->GetObject<Specie>()->GetName() << ",";
    *stream->GetStream() << dst_node->GetId() << "," << dst_node->GetObject<Specie>()->GetName() << "," << analysePacket.timestamp << "," << analysePacket.idcomm;
    *stream->GetStream() << "," << analysePacket.idseq << "," << analysePacket.dataOffset << "," << analysePacket.dataSize << "," << txTime.GetNanoSeconds();
    *stream->GetStream() << "," << analysePacket.isTCP << "," << analysePacket.isReverse << "," << infodrop << std::endl;
    } else {
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << packet->GetUid() << ",,,," ",,,," ",,,," "," << std::endl;
    }
    }
}

void PacketEventTracerSimple(Ptr<OutputStreamWrapper> stream, cbparams* cbparams_val, const std::string& infodrop, Ptr<const Node> node, Ptr<const Packet> packet, const Time& rxTime)
{
    //NS_LOG_UNCOND("RxDrop at " << Simulator::Now().GetSeconds());
    // Extract burst identifier and packet sequence number
    if (cbparams_val->m_log_condition_NodeId.minNodeId <= node->GetId()){
    resAnalysePacket analysePacket = {true, false, false, 0, 0, 0, 0, 0};
    getPacketFlux(packet, cbparams_val->m_conversion, analysePacket);
    // Log precise timestamp received of the sequence packet if needed
    if (analysePacket.succes){
    *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << packet->GetUid() << "," << node->GetId() << ","  << node->GetObject<Specie>()->GetName() << "," << analysePacket.timestamp; // we only know the node receiving/where the error occurs
    *stream->GetStream() << "," << analysePacket.idcomm << "," << analysePacket.idseq << "," << analysePacket.dataOffset << "," << analysePacket.dataSize << "," << rxTime.GetNanoSeconds();
    *stream->GetStream() << "," << analysePacket.isTCP << "," << analysePacket.isReverse << "," << infodrop << std::endl;
    } else {
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << packet->GetUid() << ",,,," ",,,," ",,," << std::endl;
    }
    }
}

void PacketEventTracerReduit(Ptr<OutputStreamWrapper> stream, cbparams* cbparams_val, const std::string& infodrop, Ptr<const Node> node, Ptr<const Packet> packet)
{
    //NS_LOG_UNCOND("RxDrop at " << Simulator::Now().GetSeconds());
    // Extract burst identifier and packet sequence number
    //This function is used to log losses. I prefer to log them all
    resAnalysePacket analysePacket = {true, false, false, 0, 0, 0, 0, 0};
    getPacketFlux(packet, cbparams_val->m_conversion, analysePacket);
    // Log precise timestamp received of the sequence packet if needed
    // this function is used for losses, I prefer to log them all
    if (analysePacket.succes){
    *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << packet->GetUid() << "," << node->GetId() << ","  << node->GetObject<Specie>()->GetName() << "," << analysePacket.timestamp; // we only know the node receiving/where the error occurs
    *stream->GetStream() << "," << analysePacket.idcomm << "," << analysePacket.idseq << "," << analysePacket.dataOffset << "," << analysePacket.dataSize;
    *stream->GetStream() << "," << analysePacket.isTCP << "," << analysePacket.isReverse << "," << infodrop << std::endl;
    } else {
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << packet->GetUid() << ",,,," ",,,," ",," << std::endl;
    }
}

void QitEventTracerReduit(Ptr<OutputStreamWrapper> stream, std::shared_ptr<cbparams> cbparams_val, const std::string& infodrop, Ptr<QueueDiscItem const> qit)
{
    //NS_LOG_UNCOND("RxDrop at " << Simulator::Now().GetSeconds());
    // Extract burst identifier and packet sequence number
    Ptr<const Node> node = cbparams_val->log_node;
    //This function is used to log losses. I prefer to log them all
    resAnalysePacket analysePacket = {true, false, false, 0, 0, 0, 0, 0};

    //never did anything so dirty until now. A better way would be to patch the ns source code, if possible ?
    Ipv4QueueDiscItem qitcpy(qit->GetPacket(), qit->GetAddress(), qit->GetProtocol(), Ipv4Header());
    mempcpy(&qitcpy, &(*qit), sizeof(Ipv4QueueDiscItem));
    qitcpy.AddHeader();
    getPacketFlux(qitcpy.GetPacket(), cbparams_val->m_conversion, analysePacket);
    // Log precise timestamp received of the sequence packet if needed
    if (analysePacket.succes){
    *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << qitcpy.GetPacket()->GetUid() << "," << node->GetId() << ","  << node->GetObject<Specie>()->GetName() << "," << analysePacket.timestamp; // we only know the node receiving/where the error occurs
    *stream->GetStream() << "," << analysePacket.idcomm << "," << analysePacket.idseq << "," << analysePacket.dataOffset << "," << analysePacket.dataSize;
    *stream->GetStream() << "," << analysePacket.isTCP << "," << analysePacket.isReverse << "," << infodrop << std::endl;
    } else {
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << qitcpy.GetPacket()->GetUid() << ",,,," ",,,," ",," << std::endl;
    }
}
}
