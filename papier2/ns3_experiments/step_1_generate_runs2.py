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
    constel_fic=dico_params.get('constellation')
    constel_fic="../config/"+constel_fic+".yaml"
    with open(constel_fic, 'r') as f:
        dico_constel=yaml.load(f, Loader=yaml.Loader)

    graine=dico_params.pop('graine')
    data_rate_megabit_per_s = dico_params.pop('debit-if-isl')
    data_rate_GSL_megabit_per_s = dico_params.pop('debit-if-gsl')
    #true_gsl_max_data_rate_megabit_per_s = data_rate_megabit_per_s*100 # used to generate bursty traffic. maybe admission control from the ground will change that 
    duration_s = int(dico_params['duree'])
    liste_params=('constellation', 'duree', 'pas', 'isls', 'sol', 'algo', 'threads')
    params=[dico_params[cle] for cle in liste_params]
    total_nb_commodites=len(list_from_to)

    list_start_time = np.zeros(total_nb_commodites, dtype=int)
    durees_prevues = np.zeros(total_nb_commodites, dtype=int)
    tcp_list_flow_size_byte = np.zeros(total_nb_commodites, dtype=int)
    udp_list_flow_size_proportion = np.zeros(total_nb_commodites)

    #setting up commodities
    random.seed(graine)
    np.random.seed(graine)
    # Both protocols
    assert "nom" not in dico_params['protocoles']
    groupes = dico_params.get('protocoles', {})
    nb_UEs = dico_params['nb-UEs-sol']
    
    offset_commodite=0
    tcp_vals=[]
    udp_vals=[]
    all_protocols_name=[]

    for nom_groupe, groupe in sorted(groupes.items()):
        #protocol_chosen=dico_params['protocoles']
        reference_rate = groupe.get("debit", data_rate_GSL_megabit_per_s['ue'])# target sending rate in Mb/s
        try:
            groupe_nb_commodites = int(groupe['nb'])
        except Exception:
            groupe_nb_commodites = round(nb_UEs*groupe.get('ratio', 2))
        if groupe_nb_commodites<=0:
            continue
        fin_groupe_commodites = offset_commodite+groupe_nb_commodites
        #setting up different start times
        decalage=12/reference_rate/10/groupe_nb_commodites # 1 MTU-packet time in ms per 10 commodities
        list_start_time_param=groupe.get('debut_ms', None)
        duree_min_ms=min(1000, int(0.5*1e3*duration_s))
        list_start_time[offset_commodite:fin_groupe_commodites]=np.linspace(start=0, stop=decalage, num=groupe_nb_commodites, endpoint=True) if list_start_time_param is None else value_or_random(list_start_time_param, groupe_nb_commodites, minmax=[0, duration_s*1e3-duree_min_ms])

        #by defaut, lasts for the whole experiment, else fixed duration, otherwise random between [0, max]
        duree=groupe.get('duree_ms', 'min,max')
        durees_prevues[offset_commodite:fin_groupe_commodites]=value_or_random(duree, groupe_nb_commodites, minmax=[np.full(groupe_nb_commodites, duree_min_ms), (int(duration_s*1e9)-list_start_time[offset_commodite:fin_groupe_commodites])//int(1e6)])
        assert all(list_start_time+durees_prevues<=duration_s*1e9)

        tcp_list_flow_size_byte[offset_commodite:fin_groupe_commodites] = (durees_prevues[offset_commodite:fin_groupe_commodites]*reference_rate/8e3).astype(int)
        udp_list_flow_size_proportion[offset_commodite:fin_groupe_commodites]=0.3*reference_rate+np.random.exponential(0.7*reference_rate, size=groupe_nb_commodites) #udp : sending rate * randomization, in Mb/s


        protocol_chosen_name=groupe['nom']
        logs_actifs=dico_params.get('logs-actifs', [])

        
        extra_parameters = groupe.get('extra_parameters', "")
        metadata=nom_groupe+groupe.get("metadata", "")

        # tcp_flow_schedule.csv
        if "tcp" == protocol_chosen_name:
            """
            Write schedule to file.

            :param filename:
            :param num_starts:                  Expected number of values in all lists
            :param list_from_to:                List of (from, to)-tuples
            :param list_flow_size_byte:         List of integer flow size (byte)
            :param list_start_time_ns:          List of integer start times (ns)
            :tcp_extra_parameters:              String (can be anything, just not containing a comma)
            :param list_metadata:               List of strings (can be anything, just not containing a comma)
            """
            for i in range(offset_commodite, fin_groupe_commodites):
                tcp_vals.append((
                    i,
                    list_from_to[i][0],
                    list_from_to[i][1],
                    tcp_list_flow_size_byte[i],
                    list_start_time[i],
                    extra_parameters,
                    metadata
                ))

        # udp_burst_schedule.csv
        elif "udp" == protocol_chosen_name:
            for i in range(offset_commodite, fin_groupe_commodites):
                udp_vals.append((i,
                            list_from_to[i][0],
                            list_from_to[i][1],
                            min(udp_list_flow_size_proportion[i], 0.999*data_rate_GSL_megabit_per_s['ue']),
                            list_start_time[i],
                            durees_prevues[i],
                            extra_parameters,
                            metadata
                        ))
        else:
            raise Exception('protocole non reconnu :',protocol_chosen_name)
        offset_commodite=fin_groupe_commodites #le groupe suivant commence là où termine ce groupe-ci
        all_protocols_name.append(protocol_chosen_name)
    assert 2*nb_UEs == offset_commodite
    assert total_nb_commodites == offset_commodite

    tcp_vals.sort(key=lambda x:x[4])#sort by start time 
    udp_vals.sort(key=lambda x:x[4])#sort by start time 
    protocols_name= '_and_'.join(sorted(np.unique(all_protocols_name)))
    run_dir  = config_ns3_properties(dico_constel, protocols_name, data_rate_megabit_per_s, data_rate_GSL_megabit_per_s, nb_UEs, params, list_from_to, logs_actifs)
    
    # Make logs_ns3 already for console.txt mapping
    local_shell.make_full_dir(run_dir + "/logs_ns3")
    # .gitignore (legacy reasons)
    local_shell.write_file(run_dir + "/.gitignore", "logs_ns3")

    if 'tcp' in all_protocols_name:
        with open(run_dir + "/tcp_flow_schedule.csv", "w+") as f_out:
            for vals in tcp_vals:
                f_out.write("{:d},{:d},{:d},{:d},{:d},{},{}\n".format(*vals))
    if 'udp' in all_protocols_name:
        with open(run_dir + "/udp_burst_schedule.csv", "w+") as f_out:
            for vals in udp_vals:
                f_out.write("{:d},{:d},{:d},{:f},{:d},{:d},{},{}\n".format(*vals))
    
    #write the commodity list in an easy place for path generation with mcnf
    local_shell.write_file("../satellite_networks_state/commodites.temp", list(zip([elt[0] for elt in list_from_to],[elt[1] for elt in list_from_to],udp_list_flow_size_proportion)))

def value_or_random(param, nb, minmax):
    """
    A function with different behaviours.
    param:
    """
    if type(param) == str:#exemples: 'min,max', '3,5'
        listeminmax = np.array(eval(param.replace('min', repr(minmax[0])).replace('max', repr(minmax[1]))))
    else:
        listeminmax = np.array(param)
    
    if listeminmax.shape in [(), (1,)]:
        assert np.all(listeminmax>=minmax[0]) and np.all(listeminmax<=minmax[1])
        return np.full(nb, int(listeminmax*1e6))
    elif listeminmax.shape == (2, nb):
        assert np.all(listeminmax>=minmax[0]) and np.all(listeminmax<=minmax[1])
        return np.array([np.random.randint(val[0]*1e6, val[1]*1e6) for val in listeminmax.transpose()], dtype=int)
    elif listeminmax.shape == (nb,):
        assert np.all(listeminmax>=minmax[0]) and np.all(listeminmax<=minmax[1])
        return np.array(listeminmax*1e6, dtype=int)
    elif listeminmax.shape in [(2,), (2, 1)]:
        assert listeminmax[0]<listeminmax[1]
        assert np.all(listeminmax[0]>=minmax[0]) and np.all(listeminmax[1]<=minmax[1])
        return np.random.randint(int(listeminmax[0]*1e6), int(listeminmax[1]*1e6), size=nb)
    else:
        raise ValueError('problème de dimension')


def config_ns3_properties(cstl_dico, protocol_chosen_name, data_rate_megabit_per_s, data_rate_GSL_megabit_per_s, nb_UEs, params, list_from_to, logs_actifs):
    #ISL network device queue size pkt for TCP, GSL network device queue size pkt for TCP
    # TCP NewReno needs at least the BDP in queue size to fulfill bandwidth
    if "tcp" in protocol_chosen_name:
        queue_size_isl_kB = int(10*data_rate_megabit_per_s)
        queue_size_gsl_kB = {cle: int(val*80/8) for cle, val in data_rate_GSL_megabit_per_s.items()} # setting Qsize to BDP : DataRate_Mbps/8 * estimated_RTT_ms = Qsize in kilobyte
        queue_size_gsl_kB['gateway']=int(queue_size_gsl_kB['gateway']/np.sqrt(nb_UEs))
    elif "udp" in protocol_chosen_name:  # UDP does not have this problem, so we cap it at 100 packets
        queue_size_isl_kB = min(10*data_rate_megabit_per_s, 100)
        queue_size_gsl_kB = {cle: min(int(val*80/8), 100) for cle, val in data_rate_GSL_megabit_per_s.items()}
    else:
        raise ValueError("Unknown protocol chosen: " + protocol_chosen_name)

    # Prepare run directory
    run_dir = "runs/run_loaded_tm_pairing_{}_Mbps_for_{}s_with_{}_{}".format(
        data_rate_megabit_per_s, params[1], protocol_chosen_name, params[5]
    )
    local_shell.remove_force_recursive(run_dir)
    local_shell.make_full_dir(run_dir)
    # config_ns3.properties
    local_shell.copy_file(
        "templates/template_config_ns3_" + protocol_chosen_name + "2.properties",
        run_dir + "/config_ns3.properties"
    )
    sat_net_dir="../../../satellite_networks_state/gen_data/{}_{}_{}_{}".format(params[0],params[3],params[4],params[5])
    with open(run_dir + "/config_ns3.properties", 'r') as f:
        lignes=f.readlines()
    replace_in_lines(lignes, "[SAT-NET-DIR]", sat_net_dir)
    replace_in_lines(lignes, "[SAT-NET-ROUTES-DIR]", sat_net_dir+"/dynamic_state_{}ms_for_{}s".format(params[2],params[1]))
    replace_in_lines(lignes, "[DYN-FSTATE-INTERVAL-UPDATE-MS]", str(params[2]))
    replace_in_lines(lignes,     "[SIMULATION-END-TIME-NS]", str(params[1] * 1000 * 1000 * 1000))
    replace_in_lines(lignes,     "[ISL-DATA-RATE-MEGABIT-PER-S]", str(data_rate_megabit_per_s))
    replace_in_lines(lignes,     "[GSL-DATA-RATE-MEGABIT-PER-S]", str(data_rate_GSL_megabit_per_s))# for ground station: /10 => a station can accept ~20% of users if gthere are 10 stations
    replace_in_lines(lignes,     "[ISL-MAX-QUEUE-SIZE-KB]", str(queue_size_isl_kB))
    replace_in_lines(lignes,     "[GSL-MAX-QUEUE-SIZE-KB]", str(queue_size_gsl_kB))

    #Traffic Control
    
    tc_obj= {obj: cstl_dico[obj]['TrafficControl'].pop('type') for obj in cstl_dico['TYPES_OBJETS_SOL'] if cstl_dico[obj].get('TrafficControl', False)}
    tc_params = [f"tc_params_{obj}={cstl_dico[obj]['TrafficControl']}" for obj in tc_obj]
    replace_in_lines(lignes,     "[TC-TYPES]", str(tc_obj))
    replace_in_lines(lignes,     "[TC-PARAMS-]", "\n".join(tc_params))
    #create the ping meshgrid with all commodities in the required format: "set(0->1, 5->6)"
    commodities_set='set(' + ', '.join(str(i) for i in range(len(list_from_to))) + ')'
    replace_in_lines(lignes,     "[SET-OF-COMMODITY-PAIRS-LOG]", commodities_set)
    commodities_set='set(' + ', '.join(f"{x[0]}->{x[1]}" for x in list_from_to) + ')'
    replace_in_lines(lignes,     "[SET-OF-COMMODITY-PAIRS-PINGMESH]", 'set()')
    #configure logs
    logs_possibles=set(('RX', 'TX', 'DROP'))
    logs_actifs=set([elt.upper() for elt in logs_actifs])
    assert logs_actifs.issubset(logs_possibles)
    for elt in logs_actifs:
        replace_in_lines(lignes,     f"ENABLE_{elt}_LOG", 'true')
    for elt in logs_possibles-logs_actifs:
        replace_in_lines(lignes,     f"ENABLE_{elt}_LOG", 'false')
    with open(run_dir + "/config_ns3.properties", 'w') as f:
        f.writelines(lignes)
    return run_dir
    
def replace_in_lines(lignes, motif, val):
    for i,l in enumerate(lignes):
        lignes[i] = l.replace(motif, val)
    return lignes
    