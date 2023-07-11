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

#include <string>

#include "topology-satellite-network.h"
#include "ns3/traffic-control-layer.h"

namespace ns3 {

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

        //Traces
        AsciiTraceHelper asciiTraceHelper;
        m_drop_stream = asciiTraceHelper.CreateFileStream (m_basicSimulation->GetLogsDir() + "/link.drops");
        *m_drop_stream->GetStream() << "instant,uid,noeud,typeObj,commId,seqNum,offset,taille,TCP,retour,info" << std::endl;
        m_tx_stream = asciiTraceHelper.CreateFileStream (m_basicSimulation->GetLogsDir() + "/link.tx");
        *m_tx_stream->GetStream() << "instant,uid,noeud,typeObj,dst,dstObj,commId,seqNum,offset,taille,dureePaquet,TCP,retour,info" << std::endl;
        m_rx_stream = asciiTraceHelper.CreateFileStream (m_basicSimulation->GetLogsDir() + "/link.rx");
        *m_rx_stream->GetStream() << "instant,uid,noeud,typeObj,commId,seqNum,offset,taille,dureePaquet,TCP,retour,info" << std::endl;
        
        // Initialize satellites
        ReadSatellites();
        std::cout << "  > Number of satellites........ " << m_nodesByType["satellite"].GetN() << std::endl;

        // Initialize ground stations
        ReadGroundObjects();
        std::cout << "  > Number of ground stations... " << m_groundStationNodes.GetN() << std::endl;

        //Only some nodes are valid endpoints
        ReadEndpoints();

        // All nodes
        std::cout << "  > Number of nodes............. " << m_allNodes.GetN() << std::endl;

        // Install internet stacks on all nodes
        InstallInternetStacks(ipv4RoutingHelper);
        std::cout << "  > Installed Internet stacks" << std::endl;

        // IP helper
        m_ipv4_helper.SetBase ("10.0.0.0", "255.255.255.0");
    
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
        
        ReadLinks();

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
        m_nodesByType["satellite"].Create(num_orbits * satellites_per_orbit);
        for (NodeContainer::Iterator n= m_nodesByType["satellite"].Begin(); n!=m_nodesByType["satellite"].End(); ++n){
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
                mobility.Install(m_nodesByType["satellite"].Get(counter));
                Ptr<MobilityModel> mobModel = m_nodesByType["satellite"].Get(counter)->GetObject<MobilityModel>();
                mobModel->SetPosition(satellite->GetPosition(satellite->GetTleEpoch()));

            } else {

                // Dynamic
                mobility.SetMobilityModel(
                        "ns3::SatellitePositionMobilityModel",
                        "SatellitePositionHelper",
                        SatellitePositionHelperValue(SatellitePositionHelper(satellite))
                );
                mobility.Install(m_nodesByType["satellite"].Get(counter));

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
        m_allNodes.Add(m_nodesByType["satellite"]);
        m_nodespecies.push_back("satellite");
    }

    void
    TopologySatelliteNetwork::ReadEndpoints()
    {
        // Only some ground nodes are valid endpoints
        auto endpoints_typelist=parse_simple_list_string(m_basicSimulation->GetConfigParamOrFail("endpoints"));
        std::string type_courant;
        for (auto itnodes = m_allNodes.Begin(); itnodes!=m_allNodes.End(); itnodes++){
            type_courant=(*itnodes)->GetObject<Specie>()->GetName();
            for (auto it_endpoints_type=endpoints_typelist.begin(); it_endpoints_type!=endpoints_typelist.end(); it_endpoints_type++){
                if (type_courant==*it_endpoints_type){
                    m_endpoints.insert((*itnodes)->GetId());
                    break;
                }
            }
        }
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
                m_nodespecies.push_back(prev_specie);
                prev_specie=specie;
                for (auto attr: m_nodesByType){
                    NS_ASSERT_MSG(attr.first != specie, "Ground devices must be grouped by type when created");
                }
                m_nodesByType[specie]=NodeContainer();
            }

            // Create ground station data holder
            Ptr<GroundStation> gs = CreateObject<GroundStation>(
                    gid, name, specie, latitude, longitude, elevation, cartesian_position
            );
            m_groundEntities.push_back(gs);

            // Create the node
            ///*
            node =CreateObject<Node>();
            m_nodesByType[specie].Add(node);
            m_allNodes.Add(node);
            node->AggregateObject(CreateObject<Specie>(specie));
            //*/
            /*
            m_groundStationNodes.Create(1);
            */
            //if (m_groundStationNodes.GetN()+m_otherGroundNodes.GetN() != gid + 1) {
            //    throw std::runtime_error("GID is not incremented each line");
            //}

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
    }

    void
    TopologySatelliteNetwork::InstallInternetStacks(const Ipv4RoutingHelper& ipv4RoutingHelper) {
        InternetStackHelper internet;
        internet.SetRoutingHelper(ipv4RoutingHelper);
        std::cout << " install stack " << std::endl;
        internet.Install(m_allNodes);
    }

    void TopologySatelliteNetwork::ReadLinks()
    {
        auto nom_liens = parse_simple_list_string(m_basicSimulation->GetConfigParamOrFail("liens"));
        std::string type_lien;
        int i=0;
        for (auto lien : nom_liens){
            type_lien=m_basicSimulation->GetConfigParamOrFail(lien+"_type");

            m_current_link_filename = format_string("lix%d.txt", i);
            auto objtypes = parse_simple_list_string(m_basicSimulation->GetConfigParamOrFail(lien+"_objets"));
            for (const auto& dev: objtypes){
                std::map<std::string, std::string> submap = parse_dict_string(m_basicSimulation->GetConfigParamOrFail(lien+"_"+dev+"_params"));//"attribute": "(nom, value)"
                m_paramaps[dev]= submap;
            }
            m_channelparams = parse_dict_string(m_basicSimulation->GetConfigParamOrFail(lien+"_params"));

            if (type_lien=="isl"){
                ReadISLs(lien);
            } else if (type_lien=="gsl"){
                ReadGSLs(lien);
            } else if (type_lien=="tl"){
                ReadTLs(lien);
            } else if (type_lien=="pyl"){
                ReadPyLs(lien);
            } else {
                throw std::runtime_error(format_string("link type %s is not defined", type_lien));
            }
            i++;
        }
    }

    void TopologySatelliteNetwork::ReadISLs(const std::string &lien)
    {
        // Link helper
        PointToPointLaserHelper p2p_laser_helper(m_paramaps);

        // Traffic control helper
        //TrafficControlHelper tch_isl;
        //tch_isl.SetRootQueueDisc("ns3::FifoQueueDisc", "MaxSize", QueueSizeValue(QueueSize("1p"))); // Will be removed later any case
        // No Traffic Control

        // Open file
        std::ifstream fs;
        std::string filename = m_satellite_network_dir + "/"+m_current_link_filename;
        if (!file_exists(filename)) {
                throw std::runtime_error(format_string("File %s does not exist.", filename.c_str()));
            }
        fs.open(filename);
        NS_ABORT_MSG_UNLESS(fs.is_open(), "File " + filename + " could not be opened");

        // Read ISL pair from each line
        std::string line;
        int counter = 0;

        std::smatch match;
        const std::regex nodeIDs("^(\\d+) (\\d+)");
        const std::regex trackLinkDrops("trackLinkDrops");
        while (std::getline(fs, line)) {

            // Retrieve satellite identifiers
            NS_ABORT_MSG_UNLESS(std::regex_search(line, match, nodeIDs), "Error parsing satellite ISL. Abort line: " << line);
            int64_t sat0_id = parse_positive_int64(match[1].str());
            int64_t sat1_id = parse_positive_int64(match[2].str());

            // Install a p2p laser link between these two satellites
            NodeContainer c;
            c.Add(m_nodesByType["satellite"].Get(sat0_id));
            c.Add(m_nodesByType["satellite"].Get(sat1_id));
            NetDeviceContainer netDevices = p2p_laser_helper.Install(c);
            
            SetErrorModel(netDevices, line);

            // Install traffic control helper
            //tch_isl.Install(netDevices.Get(0));
            //tch_isl.Install(netDevices.Get(1));

            // Assign some IP address (nothing smart, no aggregation, just some IP address)
            m_ipv4_helper.Assign(netDevices);
            m_ipv4_helper.NewNetwork();

            // Remove the traffic control layer (must be done here, else the Ipv4 helper will assign a default one)
            // no need if there is no netdevice queue interface
            //TrafficControlHelper tch_uninstaller;
            //tch_uninstaller.Uninstall(netDevices.Get(0));
            //tch_uninstaller.Uninstall(netDevices.Get(1));

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
                netDevices.Get(0)->TraceConnectWithoutContext("MacRx", MakeBoundCallback (&PacketEventTracerSimple, m_rx_stream, &m_cbparams, "ISL-rx"));
                //const std::string str_sat1 = format_string("bufOvflwLinkErr-ISL-Sat%" PRId64, sat1_id);
                netDevices.Get(1)->TraceConnectWithoutContext("MacRx", MakeBoundCallback (&PacketEventTracerSimple, m_rx_stream, &m_cbparams, "ISL-rx"));
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
                TCLogDrop(c.Get(0), netDevices.Get(0), "ISL-tc");
                TCLogDrop(c.Get(1), netDevices.Get(1), "ISL-tc");
            }

            counter += 1;
        }
        fs.close();

        // Completed
        std::cout << "    >> Created " << std::to_string(counter) << " ISL(s)" << std::endl;

    }

    void TopologySatelliteNetwork::ReadGSLs(const std::string &lien)
    {
        //for (auto attr: m_nodespecies){
        //    NS_ASSERT_MSG(m_gsl_data_rate_megabit_per_s_map.find(attr.second) != m_gsl_data_rate_megabit_per_s_map.end(), "undefined DataRate map for type"+attr.second);
        //    NS_ASSERT_MSG(m_gsl_max_queue_size_map.find(attr.second) != m_gsl_max_queue_size_map.end(), "undefined DataRate map for type"+attr.second);
        //}
        GSLHelper gsl_helper(m_paramaps);
        NetDeviceContainer devices;
        NodeContainer nodes;
        for (auto devparams: m_paramaps){
            nodes.Add(m_nodesByType[devparams.first]);
        }
        // Create and install GSL network devices 
        devices.Add(gsl_helper.Install(nodes));
        // Add callbacks. Dirty to set it here but easier than in the gsl_helper
        // uint32_t nb_sats = GetNumSatellites();
        if (m_enable_rx_log || m_enable_tx_log || m_enable_drop_log){
            for (uint32_t i=0; i< devices.GetN(); i++)
            {
                if (m_enable_drop_log) {
                    devices.Get(i)->TraceConnectWithoutContext("MacTxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "GSL-bufOvflwLinkErr")); 
                    TCLogDrop(devices.Get(i)->GetNode(), devices.Get(i), "GSL-tc");
                }
                if (m_enable_tx_log) {devices.Get(i)->TraceConnectWithoutContext("PhyTxBegin", MakeBoundCallback (&PacketEventTracer, m_tx_stream, &m_cbparams, "GSL-tx")); }
                if (m_enable_rx_log) {devices.Get(i)->TraceConnectWithoutContext("MacRx", MakeBoundCallback (&PacketEventTracerSimple, m_rx_stream, &m_cbparams, "GSL-rx")); }
            }
        }
        std::cout << "    >> Finished install GSL interfaces (interfaces, network devices, one shared channel)" << std::endl;
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

        // Check that all interfaces were created
        NS_ABORT_MSG_IF(nodes.GetN() != devices.GetN(), "Not the expected amount of interfaces has been created.");
        std::cout << "    >> GSL interfaces are setup" << std::endl;
    }

    void TopologySatelliteNetwork::ReadTLs(const std::string &lien)
    {        
        PointToPointTracenHelper p2p_helper(m_paramaps, m_channelparams);

        std::string filename = m_satellite_network_dir + "/"+m_current_link_filename;
        if (!file_exists(filename)) {
            throw std::runtime_error(format_string("File %s does not exist.", filename.c_str()));
        }
        // Read file contents
        std::string line;
        std::ifstream fstate_file(filename);
        NS_ABORT_MSG_UNLESS(fstate_file.is_open(), "File " + filename + " could not be opened");
        std::smatch match;
        const std::regex nodeIDs("^(\\d+),(\\d+)");
        const std::regex trackLinkDrops("trackLinkDrops");

        if (fstate_file) {
            while (getline(fstate_file, line)) {
                // Retrieve satellite identifiers
                NS_ABORT_MSG_UNLESS(std::regex_search(line, match, nodeIDs), "Error parsing TL nodes. Abort line: " << line);
                Ptr<Node> n1 = m_allNodes.Get(parse_positive_int64(match[1].str()));
                Ptr<Node> n2 = m_allNodes.Get(parse_positive_int64(match[2].str()));
                if (m_paramaps.find(n1->GetObject<Specie>()->GetName()) == m_paramaps.end() || m_paramaps.find(n2->GetObject<Specie>()->GetName()) == m_paramaps.end()){
                    continue;
                }

                NodeContainer p2pNodes;
                p2pNodes.Add(n1);
                p2pNodes.Add(n2);
                NetDeviceContainer p2pDevices = p2p_helper.Install(p2pNodes);

                SetErrorModel(p2pDevices, line);

                // Assign some IP address (nothing smart, no aggregation, just some IP address)
                m_ipv4_helper.Assign(p2pDevices);
                m_ipv4_helper.NewNetwork();

                // Tracking
                if (m_enable_rx_log){
                    p2pDevices.Get(0)->TraceConnectWithoutContext("MacRx", MakeBoundCallback (&PacketEventTracerSimple, m_rx_stream, &m_cbparams, "TL-rx"));
                    p2pDevices.Get(1)->TraceConnectWithoutContext("MacRx", MakeBoundCallback (&PacketEventTracerSimple, m_rx_stream, &m_cbparams, "TL-rx"));
                }
                if (m_enable_tx_log){
                    p2pDevices.Get(0)->TraceConnectWithoutContext("PhyTxBegin", MakeBoundCallback (&PacketEventTracer, m_tx_stream, &m_cbparams, "TL-tx"));
                    p2pDevices.Get(1)->TraceConnectWithoutContext("PhyTxBegin", MakeBoundCallback (&PacketEventTracer, m_tx_stream, &m_cbparams, "TL-tx"));
                }
                if (m_enable_drop_log){
                    p2pDevices.Get(0)->TraceConnectWithoutContext("MacTxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "TL-bufOvflwLinkErr"));
                    p2pDevices.Get(1)->TraceConnectWithoutContext("MacTxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "TL-bufOvflwLinkErr"));
                    TCLogDrop(n1, p2pDevices.Get(0), "TL-tc");
                    TCLogDrop(n2, p2pDevices.Get(1), "TL-tc");
                    if (std::regex_search(line, match, trackLinkDrops)){
                        //const std::string str_sat0 = format_string("channelError-ISL-Sat%" PRId64, sat0_id);
                        p2pDevices.Get(0)->TraceConnectWithoutContext("PhyRxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "TL-channelError"));
                        //const std::string str_sat1 = format_string("channelError-ISL-Sat%" PRId64, sat1_id);
                        p2pDevices.Get(1)->TraceConnectWithoutContext("PhyRxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "TL-channelError"));
                    }
                }
            }
        }
        std::cout << "    >> TL interfaces are setup" << std::endl;
    }

    
    void TopologySatelliteNetwork::ReadPyLs(const std::string &lien)
    {        
        PointToPointTracenHelper p2p_helper(m_paramaps, m_channelparams);

        std::string filename = m_satellite_network_dir + "/"+m_current_link_filename;
        if (!file_exists(filename)) {
            throw std::runtime_error(format_string("File %s does not exist.", filename.c_str()));
        }
        // Read file contents
        std::string line;
        std::ifstream fstate_file(filename);
        NS_ABORT_MSG_UNLESS(fstate_file.is_open(), "File " + filename + " could not be opened");
        std::smatch match;
        const std::regex nodeIDs("^(\\d+),(\\d+),(\\S+)");
        const std::regex trackLinkDrops("trackLinkDrops");

        if (fstate_file) {
            while (getline(fstate_file, line)) {
                NS_ABORT_MSG_UNLESS(std::regex_search(line, match, nodeIDs), "Error parsing PyL nodes. Abort line: " << line);
                Ptr<Node> n1 = m_allNodes.Get(parse_positive_int64(match[1].str()));
                Ptr<Node> n2 = m_allNodes.Get(parse_positive_int64(match[2].str()));
                p2p_helper.SetChannelAttribute("Delay", TimeValue(Time(match[3].str())));

                if (m_paramaps.find(n1->GetObject<Specie>()->GetName()) == m_paramaps.end() || m_paramaps.find(n2->GetObject<Specie>()->GetName()) == m_paramaps.end()){
                    continue;
                }

                NodeContainer p2pNodes;
                p2pNodes.Add(n1);
                p2pNodes.Add(n2);
                NetDeviceContainer pyraDevs = p2p_helper.Install(p2pNodes);

                SetErrorModel(pyraDevs, line);

                // Assign some IP address (nothing smart, no aggregation, just some IP address)
                m_ipv4_helper.Assign(pyraDevs);
                m_ipv4_helper.NewNetwork();
                // Tracking
                if (m_enable_rx_log){
                    pyraDevs.Get(0)->TraceConnectWithoutContext("MacRx", MakeBoundCallback (&PacketEventTracerSimple, m_rx_stream, &m_cbparams, "PyL-rx"));
                    pyraDevs.Get(1)->TraceConnectWithoutContext("MacRx", MakeBoundCallback (&PacketEventTracerSimple, m_rx_stream, &m_cbparams, "PyL-rx"));
                }
                if (m_enable_tx_log){
                    pyraDevs.Get(0)->TraceConnectWithoutContext("PhyTxBegin", MakeBoundCallback (&PacketEventTracer, m_tx_stream, &m_cbparams, "PyL-tx"));
                    pyraDevs.Get(1)->TraceConnectWithoutContext("PhyTxBegin", MakeBoundCallback (&PacketEventTracer, m_tx_stream, &m_cbparams, "PyL-tx"));
                }
                if (m_enable_drop_log){
                    pyraDevs.Get(0)->TraceConnectWithoutContext("MacTxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "PyL-bufOvflwLinkErr"));
                    pyraDevs.Get(1)->TraceConnectWithoutContext("MacTxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "PyL-bufOvflwLinkErr"));
                    TCLogDrop(n1, pyraDevs.Get(0), "PyL-tc");
                    TCLogDrop(n2, pyraDevs.Get(1), "PyL-tc");
                    if (std::regex_search(line, match, trackLinkDrops)){
                        //const std::string str_sat0 = format_string("channelError-ISL-Sat%" PRId64, sat0_id);
                        pyraDevs.Get(0)->TraceConnectWithoutContext("PhyRxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "PyL-channelError"));
                        //const std::string str_sat1 = format_string("channelError-ISL-Sat%" PRId64, sat1_id);
                        pyraDevs.Get(1)->TraceConnectWithoutContext("PhyRxDrop", MakeBoundCallback (&PacketEventTracerReduit, m_drop_stream, &m_cbparams, "PyL-channelError"));
                    }
                }
                
            }
        }
        std::cout << "    >> PyL interfaces are setup" << std::endl;
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
        return m_nodesByType["satellite"].GetN();
    }

    uint32_t TopologySatelliteNetwork::GetNumGroundStations() {
        return m_groundStationNodes.GetN();
    }

    
    std::vector<std::string>& TopologySatelliteNetwork::GetDevTypeVector(){
        return m_nodespecies;
    }

    const NodeContainer& TopologySatelliteNetwork::GetNodes() {
        return m_allNodes;
    }

    int64_t TopologySatelliteNetwork::GetNumNodes() {
        return m_allNodes.GetN();
    }

    const NodeContainer& TopologySatelliteNetwork::GetSatelliteNodes() {
        return m_nodesByType["satellite"];
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

    void TopologySatelliteNetwork::TCLogDrop(Ptr<Node> noeud, Ptr<NetDevice> netdev, const std::string& err_str){
        m_temp_tc = noeud->GetObject<TrafficControlLayer>();
        if (m_temp_tc){
            std::shared_ptr<cbparams> loc_cbparams = std::make_shared<cbparams>(m_cbparams);
            loc_cbparams->log_node = noeud;
            m_temp_qd = m_temp_tc->GetRootQueueDiscOnDevice(netdev);
            if (m_temp_qd){
                m_temp_qd->TraceConnectWithoutContext("Drop", MakeBoundCallback (&QitEventTracerReduit, m_drop_stream, loc_cbparams, err_str));
            }
        }
    }

}
