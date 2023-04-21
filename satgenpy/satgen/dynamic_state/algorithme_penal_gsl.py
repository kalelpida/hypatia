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
import networkx as nx 


def algorithm_penal_gsl_fw(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        endpoint_ranges,
        full_net_graph_penalised,
        interfaces,
        prev_fstate,
        is_last
    ):


    # Calculate shortest path distances
    #print("  > Calculating Floyd-Warshall for graph without ground-station relays")
    # (Note: Numpy has a deprecation warning here because of how networkx uses matrices)
    dist_net_penalgsl = nx.floyd_warshall_numpy(full_net_graph_penalised)
    # Forwarding state
    fstate = {}
    # Now write state to file for complete graph
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    #print("  > Writing forwarding state to: " + output_filename)
    with open(output_filename, "w+") as f_out:

        # Satellites to ground stations
        # From the satellites attached to the destination ground station,
        # select the one which promises the shortest path to the destination ground station (getting there + last hop)
        for curr in full_net_graph_penalised:
            for endpoint_rng in endpoint_ranges.values():
                for dst in endpoint_rng:
                    if dst==curr:
                        continue

                    # Among its neighbors, find the one which promises the
                    # lowest distance to reach the destination satellite
                    best_distance_m = 1000000000000000
                    for neighbor_id in full_net_graph_penalised.neighbors(curr):
                        distance_m = (
                                full_net_graph_penalised.edges[(curr, neighbor_id)]["weight"]
                                +
                                dist_net_penalgsl[(neighbor_id, dst)]
                        )
                        if distance_m < best_distance_m:
                            if (curr, neighbor_id) in interfaces:
                                next_hop_decision = (
                                    neighbor_id,
                                    interfaces[(curr, neighbor_id)],
                                    interfaces[(neighbor_id, curr)]
                                )
                            else:
                                #find a common channel
                                itf=full_net_graph_penalised.edges[(curr, neighbor_id)]["lix"]
                                assert ((curr, itf) in interfaces) and ((neighbor_id, itf) in interfaces)
                                next_hop_decision = (
                                    neighbor_id,
                                    interfaces[(curr, itf)],
                                    interfaces[(neighbor_id, itf)]
                                )
                            best_distance_m = distance_m
                    
                    if not prev_fstate or prev_fstate[(curr, dst)] != next_hop_decision:
                        f_out.write("%d,%d,%d,%d,%d\n" % (
                            curr,
                            dst,
                            next_hop_decision[0],
                            next_hop_decision[1],
                            next_hop_decision[2]
                        ))
                    fstate[(curr, dst)] = next_hop_decision
        
    if is_last:
        with open(output_filename+".temp", "w+") as f_out:
            f_out.write(str(fstate))

    return fstate

def algorithm_penal_gsl(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        paires,
        full_net_graph_penalised,
        interfaces,
        prev_fstate,
        is_last
    ):
    
    # Forwarding state
    fstate = {}
    # Now write state to file for complete graph
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    output_filename_chemins = output_dynamic_state_dir + "/paths_" + str(time_since_epoch_ns) + ".txt"
    #print("  > Writing forwarding state to: " + output_filename)
    with open(output_filename, "w") as f_out, open(output_filename_chemins, "w") as f_chem:

        # Satellites to ground stations
        # From the satellites attached to the destination ground station,
        # select the one which promises the shortest path to the destination ground station (getting there + last hop)
        prev_paire=[]
        prev_chemin=[]
        for paire in paires:
            dst=paire[1]
            if paire==reversed(prev_paire):
                #the graph is not oriented, so the path is reversible
                chemin=reversed(prev_chemin)
            else:
                chemin=nx.shortest_path(full_net_graph_penalised, *paire, weight="weight")
                duree=0
                #poids=0
                for ndsrc, nddst in zip(chemin[:-1], chemin[1:]):
                    duree+=full_net_graph_penalised[ndsrc][nddst]["delai"]
                    #poids+=full_net_graph_penalised[ndsrc][nddst]["weight"]
            
            f_chem.write(f"{paire},{duree},{chemin}\n")
            for curr, suiv in zip(chemin[:-1], chemin[1:]):
                next_hop_decision=(-1, -1, -1)
                if (curr, suiv) in interfaces:
                    next_hop_decision = (
                        suiv,
                        interfaces[(curr, suiv)],
                        interfaces[(suiv, curr)]
                    )
                else:
                    #find a common channel
                    itf=full_net_graph_penalised.edges[(curr, suiv)]["lix"]
                    assert ((curr, itf) in interfaces) and ((suiv, itf) in interfaces)
                    next_hop_decision = (
                        suiv,
                        interfaces[(curr, itf)],
                        interfaces[(suiv, itf)]
                    )
                if not prev_fstate or prev_fstate[(curr, dst)] != next_hop_decision:
                    f_out.write("%d,%d,%d,%d,%d\n" % (
                        curr,
                        dst,
                        next_hop_decision[0],
                        next_hop_decision[1],
                        next_hop_decision[2]
                    ))
    if is_last:
        with open(output_filename+".temp", "w+") as f_out:
            f_out.write(str(fstate))

    return fstate