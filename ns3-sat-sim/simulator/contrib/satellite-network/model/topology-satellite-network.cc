/*
 * Copyright (c) 2019 ETH Zurich
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
 * Author: Jens Eirik Saethre  June 2019
 *         Andre Aguas         March 2020
 *         Simon               2020
 */

#include "topology-satellite-network.h"
namespace ns3 {
    typedef struct {
        bool isTCP = false;
        bool isReverse = false; // wether it comes from the destination
        uint32_t dataOffset = 0;//corresponds to the fragment initial data, (o)
        uint32_t dataSize; 
        uint64_t idcomm;  
        uint64_t idseq = 0; //used in UDP, corresponds to the offset of the data sent, in packets
    } resAnalysePacket;
    
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
                p->Print(std::cerr);
                NS_ABORT_MSG("Not an usual Hypatia packet");
            }
            IdSeqHeader incomingIdSeq;
            incomingIdSeq.Deserialize(item.current);
            analysePacket.dataSize = item.currentSize;
            analysePacket.idcomm = incomingIdSeq.GetId();
            
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
            const mapflow_t conversionref = *conversion;

            // update commodity number
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

static void PacketEventTracer(Ptr<OutputStreamWrapper> stream,  cbparams* cbparams_val, const std::string& infodrop, Ptr<const Node> src_node, Ptr<const Node> dst_node,  Ptr<const Packet> packet, const Time& txTime)
{
    //NS_LOG_UNCOND("RxDrop at " << Simulator::Now().GetSeconds());
    resAnalysePacket analysePacket;
    getPacketFlux(packet, cbparams_val->m_conversion, analysePacket);
    // Log precise timestamp received of the sequence packet if needed
    *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << src_node->GetId() << "," << dst_node->GetId() << "," << analysePacket.idcomm;
    *stream->GetStream() << "," << analysePacket.idseq << "," << analysePacket.dataOffset << "," << analysePacket.dataSize << "," << txTime.GetNanoSeconds();
    *stream->GetStream() << "," << analysePacket.isTCP << "," << analysePacket.isReverse << "," << infodrop << std::endl;
}

static void PacketEventTracerReduit(Ptr<OutputStreamWrapper> stream, cbparams* cbparams_val, const std::string& infodrop, Ptr<const Node> node, Ptr<const Packet> packet)
{
    //NS_LOG_UNCOND("RxDrop at " << Simulator::Now().GetSeconds());
    // Extract burst identifier and packet sequence number
    if (cbparams_val->m_log_condition_NodeId.minNodeId >= node->GetId()){
    resAnalysePacket analysePacket;
    getPacketFlux(packet, cbparams_val->m_conversion, analysePacket);
    // Log precise timestamp received of the sequence packet if needed
    *stream->GetStream() << Simulator::Now().GetNanoSeconds() << "," << node->GetId() << ","  << analysePacket.idcomm; // we only know the node receiving/where the error occurs
    *stream->GetStream() << "," << analysePacket.idseq << "," << analysePacket.dataOffset << "," << analysePacket.dataSize; //txtime unknown
    *stream->GetStream() << "," << analysePacket.isTCP << "," << analysePacket.isReverse << "," << infodrop << std::endl;
    }
}


static void SetErrorModel(NetDeviceContainer &netDevices, std::string &line){
    static const std::regex rateErrModel("recvErrRate:(\\d*\\.?\\d*)-interval:(\\d+),(\\d+)ms");
    static const std::regex brstErrModel("brstErrMdl-brstRate:(\\d*\\.?\\d*)-brstSize:(\\d*)-interval:(\\d+),(\\d+)ms");
    static const std::regex gilbertEliottModel("gilbertElliottMdl-brstRate:(\\d*\\.?\\d*)-brstSize:(\\d*\\.?\\d*)-interval:(\\d+),(\\d+)ms");
    //static const std::regex periodicModel("periodicMdl-period:(\\d*\\.?\\d*)-recvErrRate:(\\d*\\.?\\d*)-drift:(\\d*\\.?\\d*)"); //TODO ?

    std::smatch match;
    // Error Model
    if (std::regex_search(line, match, rateErrModel)){
        //create burst error models and assign them to both devices
        double errorRate = std::atof(match[1].str().c_str());
        Ptr<RateErrorModel> em = CreateObject<RateErrorModel>();
        em->SetAttribute("ErrorRate", DoubleValue(errorRate));
        em->SetUnit(ns3::RateErrorModel::ErrorUnit::ERROR_UNIT_PACKET);
        em->Disable();
        Simulator::Schedule(MilliSeconds(std::stoi(match[2].str())), &ErrorModel::Enable, em);
        Simulator::Schedule(MilliSeconds(std::stoi(match[3].str())), &ErrorModel::Disable, em);
        netDevices.Get(0)->SetAttribute("ReceiveErrorModel", PointerValue(em));
        Ptr<RateErrorModel> em2 = CreateObject<RateErrorModel>();
        em2->SetAttribute("ErrorRate", DoubleValue(errorRate));
        em2->SetUnit(ns3::RateErrorModel::ErrorUnit::ERROR_UNIT_PACKET);
        em2->Disable();
        Simulator::Schedule(MilliSeconds(std::stoi(match[2].str())), &ErrorModel::Enable, em2);
        Simulator::Schedule(MilliSeconds(std::stoi(match[3].str())), &ErrorModel::Disable, em2);

        std::cout << "activate Rate Error Model between nodes " << netDevices.Get(0)->GetNode()->GetId() 
        << " and " << netDevices.Get(1)->GetNode()->GetId() << ", from " << match[2].str() << "ms until " << match[3].str() << "ms" << std::endl;
        netDevices.Get(1)->SetAttribute("ReceiveErrorModel", PointerValue(em2));
    } else if (std::regex_search(line, match, brstErrModel))
    {
        //create a Uniform Burst Error Model of the Channel.
        // "ErrorRate" of Burst Model is the probability to switch from Good to Bad state
        // "BurstSize" is the number of consecutive packets which will be lost. 
        //              It corresponds to maximal number of times we remain in the Bad State.
        //create random uniform variable for burst size
        Ptr<UniformRandomVariable> x = CreateObject<UniformRandomVariable> ();
        x->SetAttribute ("Min", DoubleValue (1.));
        x->SetAttribute ("Max", DoubleValue (std::atof(match[2].str().c_str())));
        double errorRate = std::atof(match[1].str().c_str());

        //create burst error models
        Ptr<BurstErrorModel> em = CreateObject<BurstErrorModel>();
        em->SetAttribute("ErrorRate", DoubleValue(errorRate));
        em->SetAttribute("BurstSize", PointerValue(x));
        em->Disable();
        Simulator::Schedule(MilliSeconds(std::stoi(match[2].str())), &ErrorModel::Enable, em);
        Simulator::Schedule(MilliSeconds(std::stoi(match[3].str())), &ErrorModel::Disable, em);
        netDevices.Get(0)->SetAttribute("ReceiveErrorModel", PointerValue(em));
        Ptr<BurstErrorModel> em2 = CreateObject<BurstErrorModel>();//did not succeeded to copy
        em2->SetAttribute("ErrorRate", DoubleValue(errorRate));
        em2->SetAttribute("BurstSize", PointerValue(x));
        em2->Disable();
        Simulator::Schedule(MilliSeconds(std::stoi(match[2].str())), &ErrorModel::Enable, em2);
        Simulator::Schedule(MilliSeconds(std::stoi(match[3].str())), &ErrorModel::Disable, em2);
        netDevices.Get(1)->SetAttribute("ReceiveErrorModel", PointerValue(em2));

        std::cout << "activate Burst Error Model between nodes " << netDevices.Get(0)->GetNode()->GetId() 
        << " and " << netDevices.Get(1)->GetNode()->GetId() << ", from " << match[2].str() << "ms until " << match[3].str() << "ms" << std::endl;
    } else if (std::regex_search(line, match, gilbertEliottModel))
    {
        //create a Gilbert Elliott Model of the Channel.
        // "ErrorRate" of Burst Model is the probability to switch from Good to Bad state
        // "BurstSize" is the number of consecutive packets which will be lost. 
        //              It corresponds to the expected number of times we remain in the Bad State.

        // First, create an exponential random variable
        // the integer part of this variable follows a geometric distribution that we use to characterize the burst size
        Ptr<WeibullRandomVariable> x = CreateObject<WeibullRandomVariable> ();
        //x->SetAttribute ("Shape", DoubleValue (1.)); //number of exponential laws, default to 1
        double lambda = std::atof(match[2].str().c_str()); //lambda param of the exponential law
        x->SetAttribute ("Scale", DoubleValue( lambda ));
        double errorRate = std::atof(match[1].str().c_str());
        //create burst error models
        Ptr<GilbEllErrorModel> em = CreateObject<GilbEllErrorModel>();
        em->SetAttribute("ErrorRate", DoubleValue(errorRate));
        em->SetAttribute("BurstSize", PointerValue(x));
        em->Disable();
        Simulator::Schedule(MilliSeconds(std::stoi(match[3].str())), &ErrorModel::Enable, em);
        Simulator::Schedule(MilliSeconds(std::stoi(match[4].str())), &ErrorModel::Disable, em);
        netDevices.Get(0)->SetAttribute("ReceiveErrorModel", PointerValue(em));
        Ptr<GilbEllErrorModel> em2 = CreateObject<GilbEllErrorModel>();
        em2->SetAttribute("ErrorRate", DoubleValue(errorRate));
        em2->SetAttribute("BurstSize", PointerValue(x));
        em2->Disable();
        Simulator::Schedule(MilliSeconds(std::stoi(match[3].str())), &ErrorModel::Enable, em2);
        Simulator::Schedule(MilliSeconds(std::stoi(match[4].str())), &ErrorModel::Disable, em2);
        netDevices.Get(1)->SetAttribute("ReceiveErrorModel", PointerValue(em2));

        std::cout << "activate Gilbert Elliott Error Model between nodes " << netDevices.Get(0)->GetNode()->GetId() 
        << " and " << netDevices.Get(1)->GetNode()->GetId() << ", from " << match[3].str() << "ms until " << match[4].str() << "ms" << std::endl;
    }
}
}
namespace ns3 {

    NS_OBJECT_ENSURE_REGISTERED (TopologySatelliteNetwork);
    TypeId TopologySatelliteNetwork::GetTypeId (void)
    {
        static TypeId tid = TypeId ("ns3::TopologySatelliteNetwork")
                .SetParent<Object> ()
                .SetGroupName("SatelliteNetwork")
        ;
        return tid;
    }

    TopologySatelliteNetwork::TopologySatelliteNetwork(Ptr<BasicSimulation> basicSimulation, const Ipv4RoutingHelper& ipv4RoutingHelper) {
        m_basicSimulation = basicSimulation;
        m_cbparams.m_conversion = new mapflow_t();
        ReadConfig();
        Build(ipv4RoutingHelper);
    }

    void TopologySatelliteNetwork::ReadConfig() {
        m_satellite_network_dir = m_basicSimulation->GetRunDir() + "/" + m_basicSimulation->GetConfigParamOrFail("satellite_network_dir");
        m_satellite_network_routes_dir =  m_basicSimulation->GetRunDir() + "/" + m_basicSimulation->GetConfigParamOrFail("satellite_network_routes_dir");
        m_satellite_network_force_static = parse_boolean(m_basicSimulation->GetConfigParamOrDefault("satellite_network_force_static", "false"));
    }

    void
    TopologySatelliteNetwork::Build(const Ipv4RoutingHelper& ipv4RoutingHelper) {
        std::cout << "SATELLITE NETWORK" << std::endl;
        std::string filename = m_basicSimulation->GetLogsDir() + "/link.drops";
        AsciiTraceHelper asciiTraceHelper;
        m_drop_stream = asciiTraceHelper.CreateFileStream (filename);

        std::string filenameDeux = m_basicSimulation->GetLogsDir() + "/link.tx";
        AsciiTraceHelper asciiTraceHelperDeux;
        m_tx_stream = asciiTraceHelperDeux.CreateFileStream (filenameDeux);

        std::string filenameTrois = m_basicSimulation->GetLogsDir() + "/link.rx";
        AsciiTraceHelper asciiTraceHelperTrois;
        m_rx_stream = asciiTraceHelperDeux.CreateFileStream (filenameTrois);
        
        // Initialize satellites
        ReadSatellites();
        std::cout << "  > Number of satellites........ " << m_satelliteNodes.GetN() << std::endl;

        // Initialize ground stations
        ReadGroundObjects();
        std::cout << "  > Number of ground stations... " << m_groundStationNodes.GetN() << std::endl;

        // Only some ground nodes are valid endpoints
        if (m_otherGroundNodes.GetN() == 0){
            for (uint32_t i = 0; i < m_groundEntities.size(); i++) {
                m_endpoints.insert(m_satelliteNodes.GetN() + i);
            }
        } else {
            auto gnd_it =m_groundEntities.begin();
            for (uint32_t i = 0; i < m_groundEntities.size(); i++) {
                if ((*gnd_it)->GetSpecie()!="gateway"){
                    m_endpoints.insert(m_satelliteNodes.GetN() + i);
                }
                gnd_it++;
            }
        }

        // All nodes
        std::cout << "  > Number of nodes............. " << m_allNodes.GetN() << std::endl;

        // Install internet stacks on all nodes
        InstallInternetStacks(ipv4RoutingHelper);
        std::cout << "  > Installed Internet stacks" << std::endl;

        // IP helper
        m_ipv4_helper.SetBase ("10.0.0.0", "255.255.255.0");

        // Link settings
        m_isl_data_rate_megabit_per_s = parse_positive_double(m_basicSimulation->GetConfigParamOrFail("isl_data_rate_megabit_per_s"));
        m_isl_max_queue_size = m_basicSimulation->GetConfigParamOrFail("isl_max_queue_size");
        m_gsl_max_queue_size_map = parse_dict_string(m_basicSimulation->GetConfigParamOrFail("gsl_max_queue_size"));
        m_gsl_data_rate_megabit_per_s_map = parse_dict_string(m_basicSimulation->GetConfigParamOrFail("gsl_data_rate_megabit_per_s"));

        // Traffic Controller Settings
        // here values are gathered by object kind
        m_tc_nodetype_qdisctype = parse_dict_string(m_basicSimulation->GetConfigParamOrDefault("tc_types", "{}"));
        for (const auto& pair: m_tc_nodetype_qdisctype){
            std::map<std::string, std::string> submap = parse_dict_string(m_basicSimulation->GetConfigParamOrFail("tc_params_"+pair.first));//"attribute": "(type, value)"
            m_tc_nodetype_attributemap[pair.first]= submap;
        }

        // Utilization tracking settings
        m_enable_isl_utilization_tracking = parse_boolean(m_basicSimulation->GetConfigParamOrFail("enable_isl_utilization_tracking"));
        if (m_enable_isl_utilization_tracking) {
            m_isl_utilization_tracking_interval_ns = parse_positive_int64(m_basicSimulation->GetConfigParamOrFail("isl_utilization_tracking_interval_ns"));
        }
        // Utilization tracking settings
        m_enable_tx_log = parse_boolean(m_basicSimulation->GetConfigParamOrDefault("enable_tx_log", "true"));
        m_enable_rx_log = parse_boolean(m_basicSimulation->GetConfigParamOrDefault("enable_rx_log", "true"));
        m_enable_drop_log = parse_boolean(m_basicSimulation->GetConfigParamOrDefault("enable_drop_log", "true"));
        m_cbparams.m_log_condition_NodeId.minNodeId = std::stoul(m_basicSimulation->GetConfigParamOrDefault("satellite_network_min_node_log", std::to_string(GetNumSatellites())));
        

        // Create ISLs
        std::cout << "  > Reading and creating ISLs" << std::endl;
        ReadISLs();

        // Create GSLs
        std::cout << "  > Creating GSLs" << std::endl;
        CreateGSLs();

        // Create TLs
        std::cout << "  > Creating Terrestrial Links" << std::endl;
        CreateTLs();

        // ARP caches
        std::cout << "  > Populating ARP caches" << std::endl;
        PopulateArpCaches();

        std::cout << std::endl;

    }

    void
    TopologySatelliteNetwork::ReadSatellites()
    {

        // Open file
        std::ifstream fs;
        fs.open(m_satellite_network_dir + "/tles.txt");
        NS_ABORT_MSG_UNLESS(fs.is_open(), "File tles.txt could not be opened");

        // First line:
        // <orbits> <satellites per orbit>
        std::string orbits_and_n_sats_per_orbit;
        std::getline(fs, orbits_and_n_sats_per_orbit);
        std::vector<std::string> res = split_string(orbits_and_n_sats_per_orbit, " ", 2);
        int64_t num_orbits = parse_positive_int64(res[0]);
        int64_t satellites_per_orbit = parse_positive_int64(res[1]);

        // Create the nodes
        m_satelliteNodes.Create(num_orbits * satellites_per_orbit);
        for (NodeContainer::Iterator n= m_satelliteNodes.Begin(); n!=m_satelliteNodes.End(); ++n){
            if (true){
                (*n)->AggregateObject(CreateObject<Specie>("satellite")); //cannot use the same object for all sats
            }
        }

        // Associate satellite mobility model with each node
        int64_t counter = 0;
        std::string name, tle1, tle2;
        while (std::getline(fs, name)) {
            std::getline(fs, tle1);
            std::getline(fs, tle2);

            // Format:
            // <name>
            // <TLE line 1>
            // <TLE line 2>

            // Create satellite
            Ptr<Satellite> satellite = CreateObject<Satellite>();
            satellite->SetName(name);
            satellite->SetTleInfo(tle1, tle2);

            // Decide the mobility model of the satellite
            MobilityHelper mobility;
            if (m_satellite_network_force_static) {

                // Static at the start of the epoch
                mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
                mobility.Install(m_satelliteNodes.Get(counter));
                Ptr<MobilityModel> mobModel = m_satelliteNodes.Get(counter)->GetObject<MobilityModel>();
                mobModel->SetPosition(satellite->GetPosition(satellite->GetTleEpoch()));

            } else {

                // Dynamic
                mobility.SetMobilityModel(
                        "ns3::SatellitePositionMobilityModel",
                        "SatellitePositionHelper",
                        SatellitePositionHelperValue(SatellitePositionHelper(satellite))
                );
                mobility.Install(m_satelliteNodes.Get(counter));

            }

            // Add to all satellites present
            m_satellites.push_back(satellite);

            counter++;
        }

        // Check that exactly that number of satellites has been read in
        if (counter != num_orbits * satellites_per_orbit) {
            throw std::runtime_error("Number of satellites defined in the TLEs does not match");
        }

        fs.close();
        m_allNodes.Add(m_satelliteNodes);
        m_devtypemap.push_back(std::make_pair(m_allNodes.GetN(), "satellite"));
    }

    void
    TopologySatelliteNetwork::ReadGroundObjects()
    {

        // Create a new file stream to open the file
        std::ifstream fs;
        fs.open(m_satellite_network_dir + "/ground_stations.txt");
        NS_ABORT_MSG_UNLESS(fs.is_open(), "File ground_stations.txt could not be opened");

        // Read ground station from each line
        std::string line;
        std::string prev_specie, specie;
        Ptr<Node> node;
        while (std::getline(fs, line)) {

            std::vector<std::string> res = split_string(line, ",", 9);

            // All eight values
            uint32_t gid = parse_positive_int64(res[0]);
            std::string name = res[1];
            double latitude = parse_double(res[2]);
            double longitude = parse_double(res[3]);
            double elevation = parse_double(res[4]);
            double cartesian_x = parse_double(res[5]);
            double cartesian_y = parse_double(res[6]);
            double cartesian_z = parse_double(res[7]);
            Vector cartesian_position(cartesian_x, cartesian_y, cartesian_z);
            specie = res[8]; //gateway, ue
            
            //update type counter
            if (prev_specie.empty()){
                prev_specie=specie;
            } else if (prev_specie!=specie){
                // assert type has not been used
                for (auto attr: m_devtypemap){
                    NS_ASSERT_MSG(attr.second != specie, "Ground devices must be grouped by type (gateway, ue)");                    
                }
                m_devtypemap.push_back(std::make_pair(m_allNodes.GetN()+m_groundStationNodes.GetN(), prev_specie));
                prev_specie=specie;
            }

            // Create ground station data holder
            Ptr<GroundStation> gs = CreateObject<GroundStation>(
                    gid, name, specie, latitude, longitude, elevation, cartesian_position
            );
            m_groundEntities.push_back(gs);

            // Create the node
            ///*
            node =CreateObject<Node>();
            if (specie=="server"){
                m_otherGroundNodes.Add(node);
            } else {
                m_groundStationNodes.Add(node);
            }
            node->AggregateObject(CreateObject<Specie>(specie));
            //*/
            /*
            m_groundStationNodes.Create(1);
            */
            if (m_groundStationNodes.GetN()+m_otherGroundNodes.GetN() != gid + 1) {
                throw std::runtime_error("GID is not incremented each line");
            }

            // Install the constant mobility model on the node
            MobilityHelper mobility;
            mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
            //mobility.Install(m_groundStationNodes.Get(gid));
            //Ptr<MobilityModel> mobilityModel = m_groundStationNodes.Get(gid)->GetObject<MobilityModel>();
            mobility.Install(node);
            Ptr<MobilityModel> mobilityModel = node->GetObject<MobilityModel>();
            mobilityModel->SetPosition(cartesian_position);

        }

        fs.close();
        m_devtypemap.push_back(std::make_pair(m_allNodes.GetN()+m_groundStationNodes.GetN(), specie));
        m_allNodes.Add(m_groundStationNodes);
        m_devtypemap.push_back(std::make_pair(m_allNodes.GetN()+m_otherGroundNodes.GetN(), "autres"));
        m_allNodes.Add(m_otherGroundNodes);
        std::cout << "    > m_devtypemap:" << std::endl;
        for (auto attr: m_devtypemap){
            std::cout << attr.first << " " << attr.second << std::endl;
        }
    }

    void
    TopologySatelliteNetwork::InstallInternetStacks(const Ipv4RoutingHelper& ipv4RoutingHelper) {
        InternetStackHelper internet;
        internet.SetRoutingHelper(ipv4RoutingHelper);
        std::cout << " install stack " << std::endl;
        internet.Install(m_allNodes);
    }

    void
    TopologySatelliteNetwork::ReadISLs()
    {

        // Link helper
        PointToPointLaserHelper p2p_laser_helper;
        p2p_laser_helper.SetQueue("ns3::DropTailQueue<Packet>", "MaxSize", QueueSizeValue(QueueSize(m_isl_max_queue_size)));
        p2p_laser_helper.SetDeviceAttribute ("DataRate", DataRateValue (DataRate (std::to_string(m_isl_data_rate_megabit_per_s) + "Mbps")));
        std::cout << "    >> ISL data rate........ " << m_isl_data_rate_megabit_per_s << " Mbit/s" << std::endl;
        std::cout << "    >> ISL max queue size... " << m_isl_max_queue_size << std::endl;

        // Traffic control helper
        TrafficControlHelper tch_isl;
        tch_isl.SetRootQueueDisc("ns3::FifoQueueDisc", "MaxSize", QueueSizeValue(QueueSize("1p"))); // Will be removed later any case

        // Open file
        std::ifstream fs;
        fs.open(m_satellite_network_dir + "/isls.txt");
        NS_ABORT_MSG_UNLESS(fs.is_open(), "File isls.txt could not be opened");

        // Read ISL pair from each line
        std::string line;
        int counter = 0;

        std::smatch match;
        const std::regex nodeIDs("(\\d+) (\\d+)");
        const std::regex trackLinkDrops("trackLinkDrops");
        while (std::getline(fs, line)) {

            // Retrieve satellite identifiers
            NS_ABORT_MSG_UNLESS(std::regex_search(line, match, nodeIDs), "Error parsing satellite ISL. Abort line: " << line);
            int64_t sat0_id = parse_positive_int64(match[1].str());
            int64_t sat1_id = parse_positive_int64(match[2].str());
            
            Ptr<Satellite> sat0 = m_satellites.at(sat0_id);
            Ptr<Satellite> sat1 = m_satellites.at(sat1_id);

            // Install a p2p laser link between these two satellites
            NodeContainer c;
            c.Add(m_satelliteNodes.Get(sat0_id));
            c.Add(m_satelliteNodes.Get(sat1_id));
            NetDeviceContainer netDevices = p2p_laser_helper.Install(c);
            
            SetErrorModel(netDevices, line);

            // Install traffic control helper
            tch_isl.Install(netDevices.Get(0));
            tch_isl.Install(netDevices.Get(1));

            // Assign some IP address (nothing smart, no aggregation, just some IP address)
            m_ipv4_helper.Assign(netDevices);
            m_ipv4_helper.NewNetwork();

            // Remove the traffic control layer (must be done here, else the Ipv4 helper will assign a default one)
            TrafficControlHelper tch_uninstaller;
            tch_uninstaller.Uninstall(netDevices.Get(0));
            tch_uninstaller.Uninstall(netDevices.Get(1));

            // Utilization tracking
            if (m_enable_isl_utilization_tracking) {
                netDevices.Get(0)->GetObject<PointToPointLaserNetDevice>()->EnableUtilizationTracking(m_isl_utilization_tracking_interval_ns);
                netDevices.Get(1)->GetObject<PointToPointLaserNetDevice>()->EnableUtilizationTracking(m_isl_utilization_tracking_interval_ns);

                m_islNetDevices.Add(netDevices.Get(0));
                m_islFromTo.push_back(std::make_pair(sat0_id, sat1_id));
                m_islNetDevices.Add(netDevices.Get(1));
                m_islFromTo.push_back(std::make_pair(sat1_id, sat0_id));
            }
            if (m_enable_rx_log){
                netDevices.Get(0)->TraceConnectWithoutContext("MacRx", MakeBoundCallback (&PacketEventTracerReduit, m_rx_stream, &m_cbparams, "ISL-rx"));
                //const std::string str_sat1 = format_string("bufOvflwLinkErr-ISL-Sat%" PRId64, sat1_id);
                netDevices.Get(1)->TraceConnectWithoutContext("MacRx", MakeBoundCallback (&PacketEventTracerReduit, m_rx_stream, &m_cbparams, "ISL-rx"));
            }
            if (m_enable_tx_log){
                netDevices.Get(0)->TraceConnectWithoutContext("PhyTxBegin", MakeBoundCallback (&PacketEventTracer, m_tx_stream, &m_cbparams, "ISL-tx"));
                netDevices.Get(1)->TraceConnectWithoutContext("PhyTxBegin", MakeBoundCallback (&PacketEventTracer, m_tx_stream, &m_cbparams, "ISL-tx"));
                /*
                m_map_FromTo_UtilizationVec[std::make_pair(sat0_id, sat1_id)] = netDevices.Get(0);
                m_map_FromTo_UtilizationVec[std::make_pair(sat1_id, sat0_id)] = netDevices.Get(1);
                */
            }

            // Tracking
            if (m_enable_drop_log){
                //const std::string str_sat0 = format_string("bufOvflwLinkErr-ISL-Sat%" PRId64, sat0_id);//could be a buffer overflow as well as a disabled link
                netDevices.Get(0)->TraceConnectWithoutContext("MacTxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "ISL-bufOvflwLinkErr"));
                //const std::string str_sat1 = format_string("bufOvflwLinkErr-ISL-Sat%" PRId64, sat1_id);
                netDevices.Get(1)->TraceConnectWithoutContext("MacTxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "ISL-bufOvflwLinkErr"));
                if (std::regex_search(line, match, trackLinkDrops)){
                    //const std::string str_sat0 = format_string("channelError-ISL-Sat%" PRId64, sat0_id);
                    netDevices.Get(0)->TraceConnectWithoutContext("PhyRxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "ISL-channelError"));
                    //const std::string str_sat1 = format_string("channelError-ISL-Sat%" PRId64, sat1_id);
                    netDevices.Get(1)->TraceConnectWithoutContext("PhyRxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "ISL-channelError"));
                }
            }

            counter += 1;
        }
        fs.close();

        // Completed
        std::cout << "    >> Created " << std::to_string(counter) << " ISL(s)" << std::endl;

    }

    void
    TopologySatelliteNetwork::CreateGSLs() {

        //for (auto attr: m_devtypemap){
        //    NS_ASSERT_MSG(m_gsl_data_rate_megabit_per_s_map.find(attr.second) != m_gsl_data_rate_megabit_per_s_map.end(), "undefined DataRate map for type"+attr.second);
        //    NS_ASSERT_MSG(m_gsl_max_queue_size_map.find(attr.second) != m_gsl_max_queue_size_map.end(), "undefined DataRate map for type"+attr.second);
        //}
        GSLHelper gsl_helper(m_devtypemap, m_tc_nodetype_qdisctype, m_tc_nodetype_attributemap);
        //std::string max_queue_size_str = format_string("%" PRId64 "p", m_gsl_max_queue_size_pkts);
        for (auto attr: m_gsl_data_rate_megabit_per_s_map){
            gsl_helper.SetDeviceAttribute(attr.first, "DataRate", DataRateValue (DataRate (attr.second + "Mbps")));
            gsl_helper.SetQueue(attr.first, "ns3::DropTailQueue<Packet>", "MaxSize", 
                    QueueSizeValue(QueueSize(m_gsl_max_queue_size_map[attr.first])));
        }
        for (auto attr: m_gsl_data_rate_megabit_per_s_map){
            std::cout << "    >> GSL data rate........ " << attr.first << " : " << attr.second << " Mbit/s" << std::endl;
        }
        for (auto attr: m_gsl_max_queue_size_map){
            std::cout << "    >> GSL max queue size... " << attr.first << " : " << attr.second << std::endl;
        }
        
        //std::cout << "    >> GSL max queue size... " << m_gsl_max_queue_size_pkts << " packets" << std::endl;

        // Traffic control helper: done in gsl_helper
        //TrafficControlHelper tch_gsl;
        //tch_gsl.SetRootQueueDisc("ns3::FifoQueueDisc", "MaxSize", QueueSizeValue(QueueSize("1p")));  // Will be removed later any case

        // Check that the file exists
        std::string filename = m_satellite_network_dir + "/gsl_interfaces_info.txt";
        if (!file_exists(filename)) {
            throw std::runtime_error(format_string("File %s does not exist.", filename.c_str()));
        }

        // Read file contents
        std::string line;
        std::ifstream fstate_file(filename);
        std::vector<std::tuple<int32_t, double>> node_gsl_if_info;
        uint32_t total_num_gsl_ifs = 0;
        if (fstate_file) {
            size_t line_counter = 0;
            while (getline(fstate_file, line)) {
                std::vector<std::string> comma_split = split_string(line, ",", 3);
                int64_t node_id = parse_positive_int64(comma_split[0]);
                int64_t num_ifs = parse_positive_int64(comma_split[1]);
                double agg_bandwidth = parse_positive_double(comma_split[2]);
                if ((size_t) node_id != line_counter) {
                    throw std::runtime_error("Node id must be incremented each line in GSL interfaces info");
                }
                node_gsl_if_info.push_back(std::make_tuple((int32_t) num_ifs, agg_bandwidth));
                total_num_gsl_ifs += num_ifs;
                line_counter++;
            }
            fstate_file.close();
        } else {
            throw std::runtime_error(format_string("File %s could not be read.", filename.c_str()));
        }
        std::cout << "    >> Read all GSL interfaces information for the " << node_gsl_if_info.size() << " nodes" << std::endl;
        std::cout << "    >> Number of GSL interfaces to create... " << total_num_gsl_ifs << std::endl;

        // Create and install GSL network devices for UEs
        NetDeviceContainer devices;
        NodeContainer uenodes;
        for (auto n = uenodes.Begin (); n != uenodes.End (); ++n)
        {
          if ((*n)->GetObject<Specie>()->GetName()=="ue"){
            uenodes.Add(*n);
          } 
        }
        // Create and install GSL network devices for Gateways
        gsl_helper.Install(m_satelliteNodes, uenodes, node_gsl_if_info);
        NodeContainer gwnodes;
        for (auto n = gwnodes.Begin (); n != gwnodes.End (); ++n)
        {
          if ((*n)->GetObject<Specie>()->GetName()=="gateway"){
            gwnodes.Add(*n);
          } 
        }
        gsl_helper.Install(m_satelliteNodes, gwnodes, node_gsl_if_info);
        devices.Add(gsl_helper.Install(m_satelliteNodes, m_groundStationNodes, node_gsl_if_info));
        // Add callbacks. Dirty to set it here but easier than in the gsl_helper
        // uint32_t nb_sats = GetNumSatellites();
        if (m_enable_rx_log || m_enable_tx_log || m_enable_drop_log){
            for (uint32_t i=0; i< devices.GetN(); i++)
            {
                if (m_enable_drop_log) {devices.Get(i)->TraceConnectWithoutContext("MacTxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "GSL-bufOvflwLinkErr")); }
                if (m_enable_tx_log) {devices.Get(i)->TraceConnectWithoutContext("PhyTxBegin", MakeBoundCallback (&PacketEventTracer, m_tx_stream, &m_cbparams, "GSL-tx")); }
                if (m_enable_rx_log) {devices.Get(i)->TraceConnectWithoutContext("MacRx", MakeBoundCallback (&PacketEventTracerReduit, m_rx_stream, &m_cbparams, "GSL-rx")); }
            }
        }
        std::cout << "    >> Finished install GSL interfaces (interfaces, network devices, one shared channel)" << std::endl;

        // Install queueing disciplines
        //tch_gsl.Install(devices);
        std::cout << "    >> Finished installing traffic control layer qdisc which will be removed later" << std::endl;

        // Assign IP addresses
        //
        // This is slow because of an inefficient implementation, if you want to speed it up, you can need to edit:
        // src/internet/helper/ipv4-address-helper.cc
        //
        // And then within function Ipv4AddressHelper::NewAddress (void), comment out:
        // Ipv4AddressGenerator::AddAllocated (addr);
        //
        // Beware that if you do this, and there are IP assignment conflicts, they are not detected.
        //
        std::cout << "    >> Assigning IP addresses..." << std::endl;
        std::cout << "       (with many interfaces, this can take long due to an inefficient IP assignment conflict checker)" << std::endl;
        std::cout << "       Progress (as there are more entries, it becomes slower):" << std::endl;
        int64_t start_time_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
        int64_t last_time_ns = start_time_ns;
        for (uint32_t i = 0; i < devices.GetN(); i++) {

            // Assign IPv4 address
            m_ipv4_helper.Assign(devices.Get(i));
            m_ipv4_helper.NewNetwork();

            // Give a progress update if at an even 10%
            int update_interval = (int) std::ceil(devices.GetN() / 10.0);
            if (((i + 1) % update_interval) == 0 || (i + 1) == devices.GetN()) {
                int64_t now_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
                printf("       - %.2f%% (t = %.2f s, update took %.2f s)\n",
                    (float) (i + 1) / (float) devices.GetN() * 100.0,
                    (now_ns - start_time_ns) / 1e9,
                    (now_ns - last_time_ns) / 1e9
                );
                last_time_ns = now_ns;
            }

        }
        std::cout << "    >> Finished assigning IPs" << std::endl;

        // Remove the traffic control layer (must be done here, else the Ipv4 helper will assign a default one)
        // useless if there is not netdevicequeueInterface
        /*
        TrafficControlHelper tch_uninstaller;
        std::cout << "    >> Removing traffic control layers (qdiscs)..." << std::endl;
        for (uint32_t i = 0; i < devices.GetN(); i++) {
            tch_uninstaller.Uninstall(devices.Get(i));
        }
        std::cout << "    >> Finished removing GSL queueing disciplines" << std::endl;
        */

        // Check that all interfaces were created
        NS_ABORT_MSG_IF(total_num_gsl_ifs != devices.GetN(), "Not the expected amount of interfaces has been created.");

        std::cout << "    >> GSL interfaces are setup" << std::endl;

    }

    void
    TopologySatelliteNetwork::CreateTLs() {

        std::string filename = m_satellite_network_dir + "/tl_interfaces_info.txt";
        if (!file_exists(filename)) {
            throw std::runtime_error(format_string("File %s does not exist.", filename.c_str()));
        }

        // Read file contents
        std::string line;
        std::ifstream fstate_file(filename);
        if (fstate_file) {
            while (getline(fstate_file, line)) {
                std::vector<std::string> comma_split = split_string(line, ",", 5);
                PointToPointTracenHelper p2p_helper;
                p2p_helper.SetQueue("ns3::DropTailQueue<Packet>", "MaxSize", QueueSizeValue(QueueSize(comma_split[4])));
                p2p_helper.SetDeviceAttribute ("DataRate", DataRateValue (DataRate (comma_split[3])));
                p2p_helper.SetChannelAttribute("Delay", TimeValue(Time(comma_split[2])));

                NodeContainer p2pNodes;
                p2pNodes.Add(m_allNodes.Get(parse_positive_int64(comma_split[0])));
                p2pNodes.Add(m_allNodes.Get(parse_positive_int64(comma_split[1])));

                NetDeviceContainer p2pDevices;
                p2pDevices = p2p_helper.Install(p2pNodes);
                // Install traffic control helper
                //tch_isl.Install(p2pDevices.Get(0));
                //tch_isl.Install(p2pDevices.Get(1));

                // Assign some IP address (nothing smart, no aggregation, just some IP address)
                m_ipv4_helper.Assign(p2pDevices);
                m_ipv4_helper.NewNetwork();

                // Remove the traffic control layer (must be done here, else the Ipv4 helper will assign a default one)
                //TrafficControlHelper tch_uninstaller;
                //tch_uninstaller.Uninstall(p2pDevices.Get(0));
                //tch_uninstaller.Uninstall(p2pDevices.Get(1));

                if (m_enable_rx_log){
                    p2pDevices.Get(0)->TraceConnectWithoutContext("MacRx", MakeBoundCallback (&PacketEventTracerReduit, m_rx_stream, &m_cbparams, "TL-rx"));
                    //const std::string str_sat1 = format_string("bufOvflwLinkErr-ISL-Sat%" PRId64, sat1_id);
                    p2pDevices.Get(1)->TraceConnectWithoutContext("MacRx", MakeBoundCallback (&PacketEventTracerReduit, m_rx_stream, &m_cbparams, "TL-rx"));
                }
                if (m_enable_tx_log){
                    p2pDevices.Get(0)->TraceConnectWithoutContext("PhyTxBegin", MakeBoundCallback (&PacketEventTracer, m_tx_stream, &m_cbparams, "TL-tx"));
                    p2pDevices.Get(1)->TraceConnectWithoutContext("PhyTxBegin", MakeBoundCallback (&PacketEventTracer, m_tx_stream, &m_cbparams, "TL-tx"));
                }

                // Tracking
                if (m_enable_drop_log){
                    //const std::string str_sat0 = format_string("bufOvflwLinkErr-ISL-Sat%" PRId64, sat0_id);//could be a buffer overflow as well as a disabled link
                    p2pDevices.Get(0)->TraceConnectWithoutContext("MacTxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "TL-bufOvflwLinkErr"));
                    //const std::string str_sat1 = format_string("bufOvflwLinkErr-ISL-Sat%" PRId64, sat1_id);
                    p2pDevices.Get(1)->TraceConnectWithoutContext("MacTxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "TL-bufOvflwLinkErr"));
                }
            }
        }

    }

    void
    TopologySatelliteNetwork::PopulateArpCaches() {

        // ARP lookups hinder performance, and actually won't succeed, so to prevent that from happening,
        // all GSL interfaces' IPs are added into an ARP cache

        // ARP cache with all ground station and satellite GSL channel interface info
        Ptr<ArpCache> arpAll = CreateObject<ArpCache>();
        arpAll->SetAliveTimeout (Seconds(3600 * 24 * 365)); // Valid one year

        // Satellite ARP entries
        for (uint32_t i = 0; i < m_allNodes.GetN(); i++) {

            // Information about all interfaces (TODO: Only needs to be GSL interfaces)
            for (size_t j = 1; j < m_allNodes.Get(i)->GetObject<Ipv4>()->GetNInterfaces(); j++) {
                Mac48Address mac48Address = Mac48Address::ConvertFrom(m_allNodes.Get(i)->GetObject<Ipv4>()->GetNetDevice(j)->GetAddress());
                Ipv4Address ipv4Address = m_allNodes.Get(i)->GetObject<Ipv4>()->GetAddress(j, 0).GetLocal();

                // Add the info of the GSL interface to the cache
                ArpCache::Entry * entry = arpAll->Add(ipv4Address);
                entry->SetMacAddress(mac48Address);

                // Set a pointer to the ARP cache it should use (will be filled at the end of this function, it's only a pointer)
                m_allNodes.Get(i)->GetObject<Ipv4L3Protocol>()->GetInterface(j)->SetAttribute("ArpCache", PointerValue(arpAll));

            }

        }

    }

    void TopologySatelliteNetwork::CollectUtilizationStatistics() {
        if (m_enable_isl_utilization_tracking) {

            // Open CSV file
            FILE* file_utilization_csv = fopen((m_basicSimulation->GetLogsDir() + "/isl_utilization.csv").c_str(), "w+");

            // Go over every ISL network device
            for (size_t i = 0; i < m_islNetDevices.GetN(); i++) {
                Ptr<PointToPointLaserNetDevice> dev = m_islNetDevices.Get(i)->GetObject<PointToPointLaserNetDevice>();
                const std::vector<double> utilization = dev->FinalizeUtilization();
                std::pair<int32_t, int32_t> src_dst = m_islFromTo[i];
                int64_t interval_left_side_ns = 0;
                for (size_t j = 0; j < utilization.size(); j++) {

                    // Only write if it is the last one, or if the utilization is different from the next
                    if (j == utilization.size() - 1 || utilization[j] != utilization[j + 1]) {

                        // Write plain to the CSV file:
                        // <src>,<dst>,<interval start (ns)>,<interval end (ns)>,<utilization 0.0-1.0>
                        fprintf(file_utilization_csv,
                                "%d,%d,%" PRId64 ",%" PRId64 ",%f\n",
                                src_dst.first,
                                src_dst.second,
                                interval_left_side_ns,
                                (j + 1) * m_isl_utilization_tracking_interval_ns,
                                utilization[j]
                        );

                        interval_left_side_ns = (j + 1) * m_isl_utilization_tracking_interval_ns;

                    }
                }
            }

            // Close CSV file
            fclose(file_utilization_csv);

        }
    }

    uint32_t TopologySatelliteNetwork::GetNumSatellites() {
        return m_satelliteNodes.GetN();
    }

    uint32_t TopologySatelliteNetwork::GetNumGroundStations() {
        return m_groundStationNodes.GetN();
    }

    
    std::vector<std::pair<uint, std::string>>& TopologySatelliteNetwork::GetDevTypeVector(){
        return m_devtypemap;
    }

    const NodeContainer& TopologySatelliteNetwork::GetNodes() {
        return m_allNodes;
    }

    int64_t TopologySatelliteNetwork::GetNumNodes() {
        return m_allNodes.GetN();
    }

    const NodeContainer& TopologySatelliteNetwork::GetSatelliteNodes() {
        return m_satelliteNodes;
    }

    const NodeContainer& TopologySatelliteNetwork::GetGroundStationNodes() {
        return m_groundStationNodes;
    }

    const std::vector<Ptr<GroundStation>>& TopologySatelliteNetwork::GetGroundStations() {
        return m_groundEntities;
    }

    const std::vector<Ptr<Satellite>>& TopologySatelliteNetwork::GetSatellites() {
        return m_satellites;
    }

    void TopologySatelliteNetwork::EnsureValidNodeId(uint32_t node_id) {
        if (node_id < 0 || node_id >= m_satellites.size() + m_groundEntities.size()) {
            throw std::runtime_error("Invalid node identifier.");
        }
    }

    bool TopologySatelliteNetwork::IsSatelliteId(uint32_t node_id) {
        EnsureValidNodeId(node_id);
        return node_id < m_satellites.size();
    }

    bool TopologySatelliteNetwork::IsGroundStationId(uint32_t node_id) {
        EnsureValidNodeId(node_id);
        return node_id >= m_satellites.size() && node_id ;
    }

    const Ptr<Satellite> TopologySatelliteNetwork::GetSatellite(uint32_t satellite_id) {
        if (satellite_id >= m_satellites.size()) {
            throw std::runtime_error("Cannot retrieve satellite with an invalid satellite ID");
        }
        Ptr<Satellite> satellite = m_satellites.at(satellite_id);
        return satellite;
    }

    uint32_t TopologySatelliteNetwork::NodeToGroundStationId(uint32_t node_id) {
        EnsureValidNodeId(node_id);
        return node_id - GetNumSatellites();
    }

    bool TopologySatelliteNetwork::IsValidEndpoint(int64_t node_id) {
        return m_endpoints.find(node_id) != m_endpoints.end();
    }

    const std::set<int64_t>& TopologySatelliteNetwork::GetEndpoints() {
        return m_endpoints;
    }

    void TopologySatelliteNetwork::RegisterFlow(std::pair<InetSocketAddress,Ipv4Address> triplet, uint64_t flowId){
        (*(m_cbparams.m_conversion))[triplet]=flowId;
    }

}
