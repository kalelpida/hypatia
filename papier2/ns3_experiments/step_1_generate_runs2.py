# The MIT License (MIT)
#
# Copyright (c) 2020 ETH Zurich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import exputil
import networkload
import random
import sys
import yaml
local_shell = exputil.LocalShell()

#local_shell.remove_force_recursive("runs")
#local_shell.remove_force_recursive("pdf")
#local_shell.remove_force_recursive("data")

# get parameters (set by hypatia/papier2/paper2.sh)
# expected parameters: debitISL constellation_file duration[s] timestep[ms] isls? Ground_stations? algorithm number_of_threads
def main_step1(list_from_to):
    config_file="../config/courante.yaml" #sys.argv[1]
    with open(config_file, 'r') as f:
        dico_params=yaml.load(f, Loader=yaml.Loader)

    graine=dico_params.pop('graine')
    data_rate_megabit_per_s = dico_params.pop('debit_isl')
    #true_gsl_max_data_rate_megabit_per_s = data_rate_megabit_per_s*100 # used to generate bursty traffic. maybe admission control from the ground will change that 
    duration_s = int(dico_params['duree'])
    liste_params=('constellation', 'duree', 'pas', 'isls', 'sol', 'algo', 'threads')
    params=[str(dico_params[cle]) for cle in liste_params]
    nb_commodites=len(list_from_to)
        



    #setting up commodities
    random.seed(graine)
    reference_rate = 1 # target sending rate in Mb/s
    list_proportion  =[random.choice(range(70,130))/100 for _ in range(nb_commodites)]
    #list_proportion  = [1 for _ in range(nb_commodites)]
    tcp_list_flow_size_byte=[int(elt*2*reference_rate*int(params[1])*(1e6/8)) for elt in list_proportion]#tcp : randomization * sending rate  * simu_duration * coeff_Mb_to_bytes
    #tcp_list_flow_size_byte=[int(reference_rate*int(params[1])*(1e6/8))]#tcp : sending rate  * simu_duration * coeff_Mb_to_bytes
    udp_list_flow_size_proportion=[elt*reference_rate for elt in list_proportion]#udp : sending rate * randomization, in Mb/s

    #setting up different start times
    coeff_decalage=1500/reference_rate*1e3/nb_commodites # MTU-packet time / nb_commodites in ns
    list_start_time = [i*coeff_decalage for i in range(nb_commodites)]

    # Both protocols
    protocol_chosen=dico_params['protocoles']
    protocol_chosen_name=protocol_chosen['nom']
    #ISL network device queue size pkt for TCP, GSL network device queue size pkt for TCP
    # TCP NewReno needs at least the BDP in queue size to fulfill bandwidth
    if protocol_chosen_name == "tcp":
        queue_size_isl_pkt = 10*data_rate_megabit_per_s
        queue_size_gsl_pkt = 10*data_rate_megabit_per_s
    elif protocol_chosen_name == "udp":  # UDP does not have this problem, so we cap it at 100 packets
        queue_size_isl_pkt = min(10*data_rate_megabit_per_s, 100)
        queue_size_gsl_pkt = min(10*data_rate_megabit_per_s, 100)
    else:
        raise ValueError("Unknown protocol chosen: " + protocol_chosen_name)

    # Prepare run directory
    run_dir = "runs/run_loaded_tm_pairing_{}_Mbps_for_{}s_with_{}_{}".format(
        data_rate_megabit_per_s, duration_s, protocol_chosen_name, params[5]
    )
    local_shell.remove_force_recursive(run_dir)
    local_shell.make_full_dir(run_dir)
    # config_ns3.properties
    local_shell.copy_file(
        "templates/template_config_ns3_" + protocol_chosen_name + "2.properties",
        run_dir + "/config_ns3.properties"
    )
    sat_net_dir="../../../satellite_networks_state/gen_data/{}_{}_{}_{}".format(params[0],params[3],params[4],params[5])
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                    "[SAT-NET-DIR]", sat_net_dir)
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                    "[SAT-NET-ROUTES-DIR]", sat_net_dir+"/dynamic_state_{}ms_for_{}s".format(params[2],params[1]))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                    "[DYN-FSTATE-INTERVAL-UPDATE-MS]", str(params[2]))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                        "[SIMULATION-END-TIME-NS]", str(duration_s * 1000 * 1000 * 1000))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                        "[ISL-DATA-RATE-MEGABIT-PER-S]", str(data_rate_megabit_per_s))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                        "[GSL-DATA-RATE-MEGABIT-PER-S]", str(reference_rate*nb_commodites*3/10))# for ground station: /10 => a station can accept ~20% of users if gthere are 10 stations
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                        "[ISL-MAX-QUEUE-SIZE-PKTS]", str(queue_size_isl_pkt))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                        "[GSL-MAX-QUEUE-SIZE-PKTS]", str(queue_size_gsl_pkt))
    #create the ping meshgrid with all commodities in the required format: "set(0->1, 5->6)"
    commodities_set='set(' + ', '.join(str(i) for i in range(nb_commodites)) + ')'
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                        "[SET-OF-COMMODITY-PAIRS-LOG]", commodities_set)
    commodities_set='set(' + ', '.join(f"{x[0]}->{x[1]}" for x in list_from_to) + ')'
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                        "[SET-OF-COMMODITY-PAIRS-PINGMESH]", 'set()')
    
    # Make logs_ns3 already for console.txt mapping
    local_shell.make_full_dir(run_dir + "/logs_ns3")

    # .gitignore (legacy reasons)
    local_shell.write_file(run_dir + "/.gitignore", "logs_ns3")

    #schedule was here !!
    # tcp_flow_schedule.csv
    if protocol_chosen_name == "tcp":
        networkload.write_schedule(
            run_dir + "/tcp_flow_schedule.csv",
            nb_commodites,
            list_from_to,
            tcp_list_flow_size_byte,
            list_start_time
        )

    # udp_burst_schedule.csv
    elif protocol_chosen_name == "udp":
        with open(run_dir + "/udp_burst_schedule.csv", "w+") as f_out:
            for i in range(nb_commodites):
                f_out.write(
                    "%d,%d,%d,%.10f,%d,%d,,%s\n" % (
                        i,
                        list_from_to[i][0],
                        list_from_to[i][1],
                        udp_list_flow_size_proportion[i],
                        i*coeff_decalage,
                        1000000000000,
                        protocol_chosen.get("metadata", "")
                    )
                )

    #write the commodity list in an easy place for path generation with mcnf
    local_shell.write_file("../satellite_networks_state/commodites.temp", list(zip([elt[0] for elt in list_from_to],[elt[1] for elt in list_from_to],udp_list_flow_size_proportion)))
