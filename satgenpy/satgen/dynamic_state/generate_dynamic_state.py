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

from satgen.distance_tools import *
from astropy import units as u
import math
import networkx as nx
import numpy as np
from .algorithme_penal_gsl import algorithm_penal_gsl

def generate_dynamic_state(
        output_dynamic_state_dir,
        epoch,
        simulation_end_time_ns,
        time_step_ns,
        offset_ns,
        satellites,
        ground_stations,
        dynamic_state_algorithm,  # Options:
                                  # "algorithm_free_one_only_gs_relays"
                                  # "algorithm_free_one_only_over_isls[2]"
                                  # "algorithm_free_gs_one_sat_many_only_over_isls[2]"
                                  # "algorithm_paired_many_only_over_isls[2]"
        net_gen_infos
):
    if offset_ns % time_step_ns != 0:
        raise ValueError("Offset must be a multiple of time_step_ns")
    prev_output = None
    is_last=False
    for time_since_epoch_ns in range(offset_ns, simulation_end_time_ns, time_step_ns):
        #tell to save complete fstate to ensure routing table continuity
        #is_last is only necessary with mcnf algorithm because a change in initialisation changes the output
        if time_since_epoch_ns == simulation_end_time_ns-time_step_ns:
            is_last=True 
        
        prev_output = generate_dynamic_state_at(
            output_dynamic_state_dir,
            epoch,
            time_since_epoch_ns,
            satellites,
            ground_stations,
            dynamic_state_algorithm, 
            prev_output,
            net_gen_infos,
            is_last
        )


def generate_dynamic_state_at(
        output_dynamic_state_dir,
        epoch,
        time_since_epoch_ns,
        satellites,
        ground_stations,
        dynamic_state_algorithm, 
        prev_output,
        net_gen_infos,
        is_last
):
    
    print("FORWARDING STATE AT T = " + (str(time_since_epoch_ns))
            + "ns (= " + str(time_since_epoch_ns / 1e9) + " seconds)")

    time = epoch + time_since_epoch_ns * u.ns
    print("  > Epoch.................. " + str(epoch))
    print("  > Time since epoch....... " + str(time_since_epoch_ns) + " ns")
    print("  > Absolute time.......... " + str(time))

    # Graphs
    full_net_graph_penalised=nx.Graph()
    
    #Add nodes
    for dev_range in net_gen_infos['dev ranges'].values():
        full_net_graph_penalised.add_nodes_from(dev_range)
    
    #Add edges
    for i, caracs_lien in enumerate(net_gen_infos['liste liens']):
        nom_lien=f"lix{i}"
        type_lien=caracs_lien[0]
        parametres = caracs_lien[2]
        if 'Delay' in parametres:
            strpoids=parametres['Delay'].split('~')[1]
            poids=float(strpoids.rstrip("msn"))
            if 'ms' in strpoids:
                poids*=1e-3
            elif 'ns' in strpoids:
                poids*=1e-9
        else:
            poids=None
        limiteDist = parametres.get("max_length_m", {})
        limitePolaire = parametres.get("polar_desactivation_anomaly_degree", {})

        if type_lien=='isl':
            for (a, b, val) in net_gen_infos['network links'][nom_lien]:
                sat_distance_m = distance_m_between_satellites(satellites[a], satellites[b], str(epoch), str(time))
                assert a in net_gen_infos['dev ranges']['satellite']
                assert b in net_gen_infos['dev ranges']['satellite']
                if limiteDist and sat_distance_m > limiteDist['satellite']:
                    raise ValueError(
                        "The distance between two satellites (%d and %d) "
                        "with an ISL exceeded the maximum ISL length (%.2fm > %.2fm at t=%dns)"
                        % (a, b, sat_distance_m, limiteDist['satellite'], time_since_epoch_ns)
                    )

                # Add to networkx graph
                if val=='s' or (not limitePolaire) or (is_connected_to_adjacent(satellites[a], seuil=limitePolaire['satellite']) and is_connected_to_adjacent(satellites[b], seuil=limitePolaire['satellite'])):
                    full_net_graph_penalised.add_edge(
                        a, b, weight=sat_distance_m/3e8 if poids==None else poids
                    )
            
        elif type_lien=='gsl':
            # What satellites can a ground station see
            for ground_station in ground_stations:
                gs_type=ground_station['type']
                if gs_type not in caracs_lien[1]:
                    continue
                # Find satellites in range
                satellites_in_range = []
                for sid in range(len(satellites)):
                    distance_m = distance_m_ground_station_to_satellite(
                        ground_station,
                        satellites[sid],
                        str(epoch),
                        str(time)
                    )
                    if (not gs_type in limiteDist) or (distance_m <= limiteDist[gs_type]):
                        satellites_in_range.append((distance_m, sid))
                satellites_in_range.sort()
                xid=len(satellites) + ground_station["gid"]
                assert xid in net_gen_infos['dev ranges'][gs_type]
                for (distance_m, sid) in satellites_in_range[:caracs_lien[1][gs_type]["maxSatellites"]]:
                    full_net_graph_penalised.add_edge(
                        sid, xid , weight=distance_m/3e8+parametres.get('penalite_s', 10) if poids==None else poids,
                        lix=nom_lien
                    )
            
        elif type_lien=='tl':
            for (a, b) in net_gen_infos['network links'][nom_lien]:
                if poids==None:
                    raise Exception("mettre à jour mesure de distance pour TLs")
                full_net_graph_penalised.add_edge(
                        a, b, weight=poids
                    )

    #################################

    #
    # Call the dynamic state algorithm which:
    #
    # (a) Output the gsl_if_bandwidth_<t>.txt files (disabled in this version)
    # (b) Output the fstate_<t>.txt files
    #
    endpoint_ranges={ x: net_gen_infos["dev ranges"][x] for x in net_gen_infos["endpoints"]}
    if dynamic_state_algorithm == "algorithm_penal_gsl":

        return algorithm_penal_gsl(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        endpoint_ranges,
        full_net_graph_penalised,
        net_gen_infos["interfaces"],
        prev_output,
        is_last
        )
        
    else:
        raise ValueError("Unknown dynamic state algorithm: " + str(dynamic_state_algorithm))
