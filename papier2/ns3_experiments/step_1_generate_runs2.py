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
import random
import sys
import numpy as np
from numpy import array #for call on eval
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
    np.random.seed(graine)
    # Both protocols
    protocol_chosen=dico_params['protocoles']
    reference_rate = protocol_chosen.get("debit", 1)# target sending rate in Mb/s

     #setting up different start times
    decalage=12/reference_rate/10/nb_commodites # 1 MTU-packet time in ms per 10 commodities
    list_start_time_param=protocol_chosen.get('debut_ms', None)
    duree_min_ms=min(1000, int(0.5*1e3*duration_s))
    list_start_time=np.linspace(start=0, stop=decalage, num=nb_commodites, endpoint=True) if list_start_time_param is None else value_or_random(list_start_time_param, nb_commodites, minmax=[0, duration_s*1e3-duree_min_ms])
    list_start_time.sort()

    #by defaut, lasts for the whole experiment, else fixed duration, otherwise random between [0, max]
    duree=protocol_chosen.get('duree_ms', 'min,max')
    durees_prevues=value_or_random(duree, nb_commodites, minmax=[np.full(nb_commodites, duree_min_ms), int(duration_s*1e3)-list_start_time//int(1e6)])
    list_end_time=list_start_time+durees_prevues
    assert all(list_end_time<=duration_s*1e9)

    tcp_list_flow_size_byte = (durees_prevues*reference_rate*8e-3).astype(int)
    udp_list_flow_size_proportion=0.3*reference_rate+np.random.exponential(0.7*reference_rate, size=nb_commodites) #udp : sending rate * randomization, in Mb/s


    protocol_chosen_name=protocol_chosen['nom']
    nb_agresseurs=protocol_chosen.get('nb_agresseurs', 0)#in case there are both TCP and UDP flows, UDP are agressors.
    #ISL network device queue size pkt for TCP, GSL network device queue size pkt for TCP
    # TCP NewReno needs at least the BDP in queue size to fulfill bandwidth
    if "tcp" in protocol_chosen_name:
        queue_size_isl_pkt = 10*data_rate_megabit_per_s
        queue_size_gsl_pkt = 10*data_rate_megabit_per_s
    elif "udp" in protocol_chosen_name:  # UDP does not have this problem, so we cap it at 100 packets
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

    # tcp_flow_schedule.csv
    if "tcp" in protocol_chosen_name:
        """
        Write schedule to file.

        :param filename:
        :param num_starts:                  Expected number of values in all lists
        :param list_from_to:                List of (from, to)-tuples
        :param list_flow_size_byte:         List of integer flow size (byte)
        :param list_start_time_ns:          List of integer start times (ns)
        :param list_extra_parameters:       List of strings (can be anything, just not containing a comma)
        :param list_metadata:               List of strings (can be anything, just not containing a comma)
        """
        list_extra_parameters=None
        list_metadata=None
        with open(run_dir + "/tcp_flow_schedule.csv", "w+") as f_out:
            for i in range(nb_commodites-protocol_chosen.get('nb_agresseurs', 0)):
                f_out.write("%d,%d,%d,%d,%d,%s,%s\n" % (
                    i,
                    list_from_to[i][0],
                    list_from_to[i][1],
                    tcp_list_flow_size_byte[i],
                    list_start_time[i],
                    list_extra_parameters[i] if list_extra_parameters is not None else "",
                    list_metadata[i] if list_metadata is not None else ""
                ))

    # udp_burst_schedule.csv
    if "udp" in protocol_chosen_name:
        list_end_time=np.full(shape=nb_commodites,fill_value=duration_s*1e9,dtype=int)
        with open(run_dir + "/udp_burst_schedule.csv", "w+") as f_out:
            if 'tcp' in protocol_chosen_name:
                #udp are aggressors
                assert nb_agresseurs >0
                i_deb_agresseurs=nb_commodites-nb_agresseurs
                #by defaut, all start near of 0, else all at instant t, otherwise random between [min, max] 
                debut_agresseurs=protocol_chosen.get('debut_agresseur_ms', list_start_time[i_deb_agresseurs:])
                duree_min_agresseur_ms=min(1000, int(0.5*1e3*duration_s))
                debuts_agresseurs_ns=value_or_random(debut_agresseurs, nb_agresseurs, minmax=[0, duration_s*1e3-duree_min_agresseur_ms])
                debuts_agresseurs_ns.sort()
                list_start_time[i_deb_agresseurs:]=debuts_agresseurs_ns

                #by defaut, lasts for the whole experiment, else fixed duration, otherwise random between [0, max]
                duree_agresseurs=protocol_chosen.get('duree_agresseur_ms', 'min,max')
                durees_agresseurs=value_or_random(duree_agresseurs, nb_agresseurs, minmax=[np.full(nb_agresseurs, duree_min_agresseur_ms), int(duration_s*1e3)-debuts_agresseurs_ns//int(1e6)])
                list_end_time[i_deb_agresseurs:]=list_start_time[i_deb_agresseurs:]+durees_agresseurs
                assert all(list_end_time<=duration_s*1e9)

                fdebit=protocol_chosen.get("debit_agresseurs", 1)
                for i in range(i_deb_agresseurs, nb_commodites):
                    f_out.write(
                        "%d,%d,%d,%.10f,%d,%d,,%s\n" % (
                            i,
                            list_from_to[i][0],
                            list_from_to[i][1],
                            udp_list_flow_size_proportion[i]*fdebit,
                            list_start_time[i],
                            list_end_time[i],
                            protocol_chosen.get("metadata", "")
                        )
                    )
            else:
                for i in range(nb_commodites):
                    f_out.write(
                        "%d,%d,%d,%.10f,%d,%d,,%s\n" % (
                            i,
                            list_from_to[i][0],
                            list_from_to[i][1],
                            udp_list_flow_size_proportion[i],
                            list_start_time[i],
                            list_end_time[i],
                            protocol_chosen.get("metadata", "")
                        )
                    )
        
    #write the commodity list in an easy place for path generation with mcnf
    local_shell.write_file("../satellite_networks_state/commodites.temp", list(zip([elt[0] for elt in list_from_to],[elt[1] for elt in list_from_to],udp_list_flow_size_proportion)))

def value_or_random(param, nb, minmax):
    """
    A function with different behaviours.
    param:
    """
    if type(param) is str:#exemples: 'min,max', '3,5'
        listeminmax = np.array(eval(param.replace('min', repr(minmax[0])).replace('max', repr(minmax[1]))))
    else:
        listeminmax = np.array(param)
    
    if listeminmax.shape in [(), (1,)]:
        assert np.all(listeminmax>=minmax[0]) and np.all(listeminmax<=minmax[1])
        return np.full(nb, int(listeminmax*1e6))
    elif listeminmax.shape == (2, nb):
        assert np.all(listeminmax>=minmax[0]) and np.all(listeminmax<=minmax[1])
        return np.array([np.random.randint(val[0]*1e6, val[1]*1e6) for val in listeminmax.transpose()], dtype=int)
    elif listeminmax.shape in [(2,), (2, 1)]:
        assert listeminmax[0]<listeminmax[1]
        assert np.all(listeminmax[0]>=minmax[0]) and np.all(listeminmax[1]<=minmax[1])
        return np.random.randint(int(listeminmax[0]*1e6), int(listeminmax[1]*1e6), size=nb)
    else:
        raise ValueError('problème de dimension')
    