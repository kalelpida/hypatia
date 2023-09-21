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
    bool isTCP;
    bool isReverse; // wether it comes from the destination
    uint32_t dataOffset;//corresponds to the fragment initial data, (o)
    uint32_t dataSize; 
    uint64_t idcomm;  
    uint64_t idseq; //used in UDP, corresponds to the offset of the data sent, in packets
    uint32_t timestamp;//TCP option timestamp
    //uint32_t ackseq;//TCP sequence number (to be acked by other)
    //uint32_t ackno;//TCP ack number
    Ptr<const Node> srcNode; // IP source
    Ptr<const Node> dstNode; // IP dest
    };

typedef struct structresAnalysePacket resAnalysePacket;

enum NiveauDeReponse { RIEN, IP, TRANSPORT };

static NiveauDeReponse getPacketInfos(Ptr<const Packet> p, cbparams* cbparams_val, resAnalysePacket& analysePacket){
    // Extract burst identifier and packet sequence number if UDP
    // Otherwise get flow identifier from packet sequence number
    static TypeId tidInteret= IdSeqHeader::GetTypeId();
    static TypeId tidtcpheader = TcpHeader::GetTypeId();
    static TypeId tidipheader = Ipv4Header::GetTypeId();
    static TypeId tidudpheader = UdpHeader::GetTypeId();

    // initalize result struct
    analysePacket.isTCP = false;
    analysePacket.isReverse=false;
    analysePacket.dataOffset=0;
    analysePacket.timestamp=0;
    analysePacket.idseq = 0;
    analysePacket.dataSize=0;

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
            analysePacket.srcNode = (*cbparams_val->mapnode).at(ipheader.GetSource()); 
            idDest.SetIpv4(ipheader.GetDestination());
            analysePacket.dstNode = (*cbparams_val->mapnode).at(ipheader.GetDestination());
            break;
        }
    }
    if (! it.HasNext()){
        p->Print(std::cerr);
        NS_ABORT_MSG("incomplete packet");
        return NiveauDeReponse::RIEN;
    }
    item = it.Next ();  
    if (item.tid == tidudpheader){
        // that's UDP
        
        /*
        UdpHeader udpheader;
        udpheader.Deserialize(item.current);
        std::get<1>(idSource) = udpheader.GetSourcePort();
        std::get<1>(idDest) = udpheader.GetDestinationPort();
        */
        
        // analysePaquet.isReverse= false;  // there is no way back in standard UDP
        if (! it.HasNext()){
            p->Print(std::cerr);
            NS_ABORT_MSG("incomplete packet");
        }
        item = it.Next ();
        if (item.tid!=tidInteret) {
            return NiveauDeReponse::IP;//inintéressant, sans doute du ping
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
        return NiveauDeReponse::TRANSPORT;
    
    } else if (item.tid == tidtcpheader){
        TcpHeader tcpheader;
        analysePacket.isTCP = true;
        tcpheader.Deserialize(item.current);

        TcpHeader::TcpOptionList tcp_option_list = tcpheader.GetOptionList();
        for (auto it = tcp_option_list.rbegin (); it != tcp_option_list.rend (); ++it){
        if ((*it)->GetKind () == TcpOption::TS)
            {
            Ptr<const TcpOptionTS> ts = DynamicCast<const TcpOptionTS>(*it);
            analysePacket.timestamp=ts->GetTimestamp();
            }
        }

        idSource.SetPort(tcpheader.GetSourcePort());
        idDest.SetPort(tcpheader.GetDestinationPort());
        uint8_t tcpflags =tcpheader.GetFlags ();

        // update commodity number
        const mapflow_t conversionref = *cbparams_val->mapflow;
        bool trouve=false;
        auto quadruplet = std::make_pair(idSource, idDest);
        auto quadruplet_reverse = std::make_pair(idDest, idSource);
        for (auto paire : conversionref){
            if ( paire.first == quadruplet){
                analysePacket.idcomm = paire.second;
                // analysePacket.isReverse = false;
                trouve=true;
                break;
            } else if (paire.first == quadruplet_reverse){
                analysePacket.idcomm = paire.second;
                analysePacket.isReverse = true;
                trouve=true;
                break;
            }
        }
        
        if (!trouve){
            // when the socket was created, the interface to send the syn packet was not chosen, neither the IP address
            if (tcpflags & (TcpHeader::SYN | TcpHeader::ACK)){
                // This is surely part of the 3 way TCP handshake.
                // I could not find a simple way to check it, because flows will connect to the same port numberflow won't be established before TCP connection
                return NiveauDeReponse::IP;
            }
            std::cout << "New packet received:" << std::endl;
            p->Print(std::cout);
            std::cout << "\n Until now, only " << conversionref.size() <<" below commodities are listed" << std::endl;

            for (auto paire : conversionref){
                std::cout << "src" << paire.first.first.GetIpv4() << ":" << paire.first.first.GetPort() << " ; dst " << paire.first.second.GetIpv4() << ":" << paire.first.second.GetPort() << " ; related commodity: " << paire.second << std::endl;
            }
            NS_ABORT_MSG("Not recognised TCP packet:");
        }
        
        
        // update data info carried by the packet
        if (it.HasNext()){
            item = it.Next();
            NS_ASSERT_MSG(item.type == PacketMetadata::Item::ItemType::PAYLOAD, "not an usual Hypatia TCP packet");
            analysePacket.dataOffset = item.currentTrimedFromStart;
            analysePacket.dataSize = item.currentSize;
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
    return NiveauDeReponse::TRANSPORT;
}

void PacketEventTracer(Ptr<OutputStreamWrapper> stream,  cbparams* cbparams_val, const std::string& evenement, Ptr<const Node> src_node, Ptr<const Node> dst_node,  Ptr<const Packet> packet, const Time& txTime)
{
    //NS_LOG_UNCOND("RxDrop at " << Simulator::Now().GetSeconds());
    resAnalysePacket analysePacket;
    // Log precise timestamp received of the sequence packet if needed
    switch (getPacketInfos(packet, cbparams_val, analysePacket))
    {
    case NiveauDeReponse::TRANSPORT:
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << packet->GetUid() << "," << src_node->GetId() << "," << src_node->GetObject<Specie>()->GetName() << ",";
        *stream->GetStream() << dst_node->GetId() << "," << dst_node->GetObject<Specie>()->GetName() << "," << analysePacket.timestamp << "," << analysePacket.idcomm;
        *stream->GetStream() << "," << analysePacket.idseq << "," << analysePacket.dataOffset << "," << analysePacket.dataSize << "," << txTime.GetNanoSeconds();
        *stream->GetStream() << "," << analysePacket.isTCP << "," << analysePacket.isReverse << "," << evenement << std::endl;
        break;
    case NiveauDeReponse::IP:
    case NiveauDeReponse::RIEN:
    default:
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << packet->GetUid() << ",,,," ",,,," ",," <<  txTime.GetNanoSeconds() << ",,," << evenement << std::endl;
        break;
    }
}

void PacketEventTracerSimple(Ptr<OutputStreamWrapper> stream, cbparams* cbparams_val, const std::string& evenement, Ptr<const Node> node, Ptr<const Packet> packet, const Time& rxTime)
{
    resAnalysePacket analysePacket;
    // Log precise timestamp received of the sequence packet if needed
    switch (getPacketInfos(packet, cbparams_val, analysePacket))
    {
    case NiveauDeReponse::TRANSPORT:
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << packet->GetUid() << "," << node->GetId() << ","  << node->GetObject<Specie>()->GetName() << "," << analysePacket.timestamp; // we only know the node receiving/where the error occurs
        *stream->GetStream() << "," << analysePacket.idcomm << "," << analysePacket.idseq << "," << analysePacket.dataOffset << "," << analysePacket.dataSize << "," << rxTime.GetNanoSeconds();
        *stream->GetStream() << "," << analysePacket.isTCP << "," << analysePacket.isReverse << "," << evenement << std::endl;
        break;
    case NiveauDeReponse::IP:// Here we can log the IP src and dst node
    case NiveauDeReponse::RIEN:
    default:
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << packet->GetUid() << "," << node->GetId() << ","  << node->GetObject<Specie>()->GetName() << ",,," ",,," ",,," << evenement << std::endl;
        break;
    }
}

void PacketEventTracerReduit(Ptr<OutputStreamWrapper> stream, cbparams* cbparams_val, const std::string& evenement, Ptr<const Node> node, Ptr<const Packet> packet)
{
    //This function is used to log losses.
    resAnalysePacket analysePacket;
    // Log precise timestamp received of the sequence packet if needed

    
    switch (getPacketInfos(packet, cbparams_val, analysePacket))
    {
    case NiveauDeReponse::TRANSPORT:
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << packet->GetUid() << "," << node->GetId() << ","  << node->GetObject<Specie>()->GetName() << "," << analysePacket.timestamp; // we only know the node receiving/where the error occurs
        *stream->GetStream() << "," << analysePacket.idcomm << "," << analysePacket.idseq << "," << analysePacket.dataOffset << "," << analysePacket.dataSize;
        *stream->GetStream() << "," << analysePacket.isTCP << "," << analysePacket.isReverse << "," << evenement << std::endl;
        break;
    case NiveauDeReponse::IP:
    case NiveauDeReponse::RIEN:
    default:
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << packet->GetUid() << ",,,," ",,,," ",," << evenement << std::endl;
        break;
    }
}

void QitEventTracerReduit(Ptr<OutputStreamWrapper> stream, cbparams * cbparams_val, const std::string &evenement, Ptr<QueueDiscItem const> qit)
{
    //NS_LOG_UNCOND("RxDrop at " << Simulator::Now().GetSeconds());
    // Extract burst identifier and packet sequence number
    Ptr<const Node> node = cbparams_val->log_node;
    //This function is used to log losses. I prefer to log them all
    resAnalysePacket analysePacket;
    //never did anything so dirty until now. A better way would be to patch the ns source code, if possible ?
    Ipv4QueueDiscItem qitcpy(qit->GetPacket(), qit->GetAddress(), qit->GetProtocol(), Ipv4Header());
    mempcpy(&qitcpy, &(*qit), sizeof(Ipv4QueueDiscItem));
    qitcpy.AddHeader();
    // Log precise timestamp received of the sequence packet if needed
    switch (getPacketInfos(qitcpy.GetPacket(), cbparams_val, analysePacket))
    {
    case NiveauDeReponse::TRANSPORT:
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << qitcpy.GetPacket()->GetUid() << "," << node->GetId() << ","  << node->GetObject<Specie>()->GetName() << "," << analysePacket.timestamp; // we only know the node receiving/where the error occurs
        *stream->GetStream() << "," << analysePacket.idcomm << "," << analysePacket.idseq << "," << analysePacket.dataOffset << "," << analysePacket.dataSize;
        *stream->GetStream() << "," << analysePacket.isTCP << "," << analysePacket.isReverse << "," << evenement << std::endl;
        break;
    case NiveauDeReponse::IP:
    case NiveauDeReponse::RIEN:
    default:
        *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << qitcpy.GetPacket()->GetUid() << ",,,," ",,,," ",," << evenement << std::endl;
        break;
    }
}
} //namespace ns3
