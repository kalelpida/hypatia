/*
 * Copyright (c) 2020 ETH Zurich
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
 * Author: Simon               2020
 */

#include "gsl-if-bandwidth-helper.h"

namespace ns3 {

    GslIfBandwidthHelper::GslIfBandwidthHelper (Ptr<BasicSimulation> basicSimulation, NodeContainer nodes, std::vector<std::pair<uint, std::string>>& devtypemap) {
        std::cout << "SETUP GSL IF BANDWIDTH HELPER" << std::endl;
        m_basicSimulation = basicSimulation;
        m_devtypemap = devtypemap;
        m_nodes = nodes;
        m_gsl_data_rate_megabit_per_s_map = parse_dict_string(m_basicSimulation->GetConfigParamOrFail("gsl_data_rate_megabit_per_s"));

        // Load first forwarding state
        m_dynamicStateUpdateIntervalNs = parse_positive_int64(m_basicSimulation->GetConfigParamOrFail("dynamic_state_update_interval_ns"));
        std::cout << "  > GSL interface bandwidth update interval: " << m_dynamicStateUpdateIntervalNs << "ns" << std::endl;
        std::cout << "  > Perform first GSL interface bandwidth setting for t=0" << std::endl;
        UpdateGslIfBandwidth(0);
        basicSimulation->RegisterTimestamp("Set first GSL interface bandwidth");

        std::cout << std::endl;
    }

    void GslIfBandwidthHelper::UpdateGslIfBandwidth(int64_t t) {

        // Filename
        std::ostringstream res;
        res << m_basicSimulation->GetRunDir() << "/";
        res << m_basicSimulation->GetConfigParamOrFail("satellite_network_routes_dir") << "/gsl_if_bandwidth_" << t << ".txt";
        std::string filename = res.str();

        // Check that the file exists
        if (!file_exists(filename)) {
            throw std::runtime_error(format_string("File %s does not exist.", filename.c_str()));
        }

        // Open file
        std::string line;
        std::ifstream fstate_file(filename);
        if (fstate_file) {

            // Go over each line
            size_t line_counter = 0;
            auto devtypeiterator = m_devtypemap.begin();
            double m_gsl_data_rate_megabit_per_s;
            while (getline(fstate_file, line)) {

                // Split on ,
                std::vector<std::string> comma_split = split_string(line, ",", 3);

                // Retrieve node identifiers
                int64_t node_id = parse_positive_int64(comma_split[0]);
                int64_t if_id = parse_positive_int64(comma_split[1]);
                double bandwidth_fraction = parse_positive_double(comma_split[2]);

                // Check the node
                NS_ABORT_MSG_IF(node_id < 0 || node_id >= m_nodes.GetN(), "Invalid node id.");

                // Check the interface
                NS_ABORT_MSG_IF(if_id < 0 || if_id + 1 >= m_nodes.Get(node_id)->GetObject<Ipv4>()->GetNInterfaces(), "Invalid interface");

                // Change the device type param (satellite, ue, gateway.)
                while (node_id >= devtypeiterator->first){
                    devtypeiterator++;
                    m_gsl_data_rate_megabit_per_s = std::stod(m_gsl_data_rate_megabit_per_s_map[devtypeiterator->second]);
                }

                // Set data rate (the ->GetObject<GSLNetDevice>() will fail if it is not a GSL network device)
                m_nodes.Get(node_id)->GetObject<Ipv4>()->GetNetDevice(1 + if_id)->GetObject<GSLNetDevice>()->SetDataRate(
                        DataRate (std::to_string( m_gsl_data_rate_megabit_per_s * bandwidth_fraction) + "Mbps")
                );

                // Next line
                line_counter++;

            }

            // Close file
            fstate_file.close();

        } else {
            throw std::runtime_error(format_string("File %s could not be read.", filename.c_str()));
        }

        // Given that this code will only be used with satellite networks, this is okay-ish,
        // but it does create a very tight coupling between the two -- technically this class
        // can be used for other purposes as well
        if (!parse_boolean(m_basicSimulation->GetConfigParamOrDefault("satellite_network_force_static", "false"))) {
            int64_t next_update_ns = t + m_dynamicStateUpdateIntervalNs;
            if (next_update_ns < m_basicSimulation->GetSimulationEndTimeNs()) {
                Simulator::Schedule(NanoSeconds(m_dynamicStateUpdateIntervalNs), &GslIfBandwidthHelper::UpdateGslIfBandwidth, this, next_update_ns);
            }
        }

    }

} // namespace ns3
