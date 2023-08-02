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

#ifndef TOPOLOGY_SATELLITE_NETWORK_H
#define TOPOLOGY_SATELLITE_NETWORK_H

#include <utility>
#include "ns3/core-module.h"
#include "ns3/node.h"
#include "ns3/node-container.h"
#include "ns3/topology.h"
#include "ns3/exp-util.h"
#include "ns3/basic-simulation.h"
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
//#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/random-variable-stream.h"
#include "ns3/command-line.h"
#include "ns3/traffic-control-helper.h"
#include "ns3/ground-station.h"
#include "ns3/satellite-position-helper.h"
#include "ns3/satellite-position-mobility-model.h"
#include "ns3/mobility-helper.h"
#include "ns3/string.h"
#include "ns3/type-id.h"
#include "ns3/vector.h"
#include "ns3/satellite-position-helper.h"
#include "ns3/mobility-helper.h"
#include "ns3/mobility-model.h"
#include "ns3/ipv4-static-routing-helper.h"
#include "ns3/ipv4-static-routing.h"
#include "ns3/ipv4-routing-table-entry.h"
#include "ns3/wifi-net-device.h"
#include "ns3/ipv4.h"
#include <regex>
#include "ns3/id-seq-header.h"
#include "ns3/states-error-model.h"
#include "ns3/simulator.h" // for scheduling in SetErrorModel
#include "ns3/specie.h"

//devices
#include "ns3/point-to-point-laser-net-device.h"
#include "ns3/point-to-point-laser-helper.h"
#include "ns3/gsl-helper.h"
#include "ns3/point-to-point-tracen-helper.h"
#include "ns3/point-to-point-tracen-net-device.h"
#include "ns3/point-to-point-tracen-channel.h"
#include "point-to-point-tracen-remote-channel.h"

#include "ns3/trace-journal.h"
#include "ns3/trace-etats.h"

#include <memory> //for shared_ptr
namespace ns3 {
    

    class TopologySatelliteNetwork : public Topology
    {
    public:

        // Constructors
        static TypeId GetTypeId (void);
        TopologySatelliteNetwork(Ptr<BasicSimulation> basicSimulation, const Ipv4RoutingHelper& ipv4RoutingHelper);

        // Inherited accessors
        const NodeContainer& GetNodes();
        int64_t GetNumNodes();
        bool IsValidEndpoint(int64_t node_id);
        const std::set<int64_t>& GetEndpoints();
        void RegisterFlow(std::pair<InetSocketAddress,Ipv4Address> triplet, uint64_t flowId);

        // Additional accessors
        uint32_t GetNumSatellites();
        uint32_t GetNumGroundStations();
        std::vector<std::string>& GetDevTypeVector();
        const NodeContainer& GetSatelliteNodes();
        const NodeContainer& GetGroundStationNodes();
        const std::vector<Ptr<GroundStation>>& GetGroundStations();
        const std::vector<Ptr<Satellite>>& GetSatellites();
        const Ptr<Satellite> GetSatellite(uint32_t sat_id);
        uint32_t NodeToGroundStationId(uint32_t node_id);
        bool IsSatelliteId(uint32_t node_id);
        bool IsGroundStationId(uint32_t node_id);

        // Post-processing
        void CollectUtilizationStatistics();

    private:

        // Build functions
        void ReadConfig();
        void Build(const Ipv4RoutingHelper& ipv4RoutingHelper);
        void ReadGroundObjects();
        void ReadSatellites();
        void ReadEndpoints();
        void ReadLinks();
        void InstallInternetStacks(const Ipv4RoutingHelper& ipv4RoutingHelper);
        void ReadISLs(const std::string& lien);
        void ReadGSLs(const std::string& lien);
        void ReadTLs(const std::string& lien);
        void ReadPyLs(const std::string& lien);

        // Helper
        void EnsureValidNodeId(uint32_t node_id);

        // Routing
        Ipv4AddressHelper m_ipv4_helper;
        void PopulateArpCaches();

        // Log
        void TCLogDrop(Ptr<Node> noeud, Ptr<NetDevice> netdev, const std::string& err_str); //for Traffic Control

        // Input
        Ptr<BasicSimulation> m_basicSimulation;       //<! Basic simulation instance
        std::string m_satellite_network_dir;          //<! Directory containing satellite network information
        std::string m_satellite_network_routes_dir;   //<! Directory containing the routes over time of the network
        bool m_satellite_network_force_static;        //<! True to disable satellite movement and basically run
                                                      //   it static at t=0 (like a static network)

        // Generated state
        NodeContainer m_allNodes;                           //!< All nodes
        NodeContainer m_groundStationNodes;                 //!< GSL capable nodes
        NodeContainer m_otherGroundNodes;                 //!< Ground station nodes
        NodeContainer m_satelliteNodes;                     //!< Satellite nodes
        std::map<std::string, NodeContainer> m_nodesByType; //!< All nodes by type
        std::vector<Ptr<GroundStation> > m_groundEntities;  //!< all ground entities
        std::vector<Ptr<Satellite>> m_satellites;           //<! Satellites
        std::set<int64_t> m_endpoints;                      //<! Endpoint ids = ground station ids

        // ISL devices
        NetDeviceContainer m_islNetDevices;
        std::vector<std::pair<int32_t, int32_t>> m_islFromTo;
        //std::map<std::pair<int32_t, int32_t>, Ptr<std::vector<double>>> m_map_FromTo_UtilizationVec;

        // Values
        //Net Device
        double m_isl_data_rate_megabit_per_s;
        std::map<std::string, std::string> m_gsl_data_rate_megabit_per_s_map;
        std::string m_isl_max_queue_size;
        std::map<std::string, std::string> m_gsl_max_queue_size_map;

        //Traffic Controller
        std::map<std::string, std::string> m_tc_nodetype_qdisctype;
        std::map< std::string, std::map<std::string, std::string>> m_tc_nodetype_attributemap;

        bool m_enable_isl_utilization_tracking;
        std::set<std::string> m_enabled_tx_log, m_enabled_rx_log, m_enabled_drop_log, m_enabled_q_log;
        int64_t m_isl_utilization_tracking_interval_ns;
        std::vector<std::string> m_nodespecies;

        Ptr<OutputStreamWrapper> m_drop_stream; //!< stream where to log drop events
        Ptr<OutputStreamWrapper> m_tx_stream; //!< stream where to log transmission events
        Ptr<OutputStreamWrapper> m_rx_stream; //!< stream where to log receive events
        Ptr<OutputStreamWrapper> m_q_stream; //!< stream where to log q stats

        cbparams m_cbparams;
        Time m_qlog_update_interval;

        std::string m_current_link_filename;
        std::map<std::string, std::string> m_channelparams;
        std::map<std::string, std::map<std::string, std::string>> m_paramaps;
        Ptr<TrafficControlLayer> m_temp_tc;
        Ptr<QueueDisc> m_temp_qd;
    };
}

#endif //TOPOLOGY_SATELLITE_NETWORK_H
