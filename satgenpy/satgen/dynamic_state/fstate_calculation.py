import math
import networkx as nx
from ..dynamic_mcnf_paper_code.interface import calcul_paths

def calculate_fstate_shortest_path_without_gs_relaying(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph_only_satellites_with_isls,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        ground_station_satellites_in_range_candidates,
        sat_neighbor_to_if,
        prev_fstate,
        enable_verbose_logs,
        is_last
):

    # Calculate shortest path distances
    if enable_verbose_logs:
        print("  > Calculating Floyd-Warshall for graph without ground-station relays")
    # (Note: Numpy has a deprecation warning here because of how networkx uses matrices)
    dist_sat_net_without_gs = nx.floyd_warshall_numpy(sat_net_graph_only_satellites_with_isls)

    # Forwarding state
    fstate = {}

    # Now write state to file for complete graph
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    if enable_verbose_logs:
        print("  > Writing forwarding state to: " + output_filename)
    with open(output_filename, "w+") as f_out:

        # Satellites to ground stations
        # From the satellites attached to the destination ground station,
        # select the one which promises the shortest path to the destination ground station (getting there + last hop)
        dist_satellite_to_ground_station = {}
        for curr in range(num_satellites):
            for dst_gid in range(num_ground_stations):
                dst_gs_node_id = num_satellites + dst_gid

                # Among the satellites in range of the destination ground station,
                # find the one which promises the shortest distance
                possible_dst_sats = ground_station_satellites_in_range_candidates[dst_gid]
                possibilities = []
                for b in possible_dst_sats:
                    if not math.isinf(dist_sat_net_without_gs[(curr, b[1])]):  # Must be reachable
                        possibilities.append(
                            (
                                dist_sat_net_without_gs[(curr, b[1])] + b[0],
                                b[1]
                            )
                        )
                #possibilities = list(sorted(possibilities))
                #end station must connect to the nearest satellite
                possibilities = list(sorted(ground_station_satellites_in_range_candidates[dst_gid]))

                # By default, if there is no satellite in range for the
                # destination ground station, it will be dropped (indicated by -1)
                next_hop_decision = (-1, -1, -1)
                distance_to_ground_station_m = float("inf")
                if len(possibilities) > 0:
                    dst_sat = possibilities[0][1]
                    distance_to_ground_station_m = possibilities[0][0]

                    # If the current node is not that satellite, determine how to get to the satellite
                    if curr != dst_sat:

                        # Among its neighbors, find the one which promises the
                        # lowest distance to reach the destination satellite
                        best_distance_m = 1000000000000000
                        for neighbor_id in sat_net_graph_only_satellites_with_isls.neighbors(curr):
                            distance_m = (
                                    sat_net_graph_only_satellites_with_isls.edges[(curr, neighbor_id)]["weight"]
                                    +
                                    dist_sat_net_without_gs[(neighbor_id, dst_sat)]
                            )
                            if distance_m < best_distance_m:
                                next_hop_decision = (
                                    neighbor_id,
                                    sat_neighbor_to_if[(curr, neighbor_id)],
                                    sat_neighbor_to_if[(neighbor_id, curr)]
                                )
                                best_distance_m = distance_m

                    else:
                        # This is the destination satellite, as such the next hop is the ground station itself
                        next_hop_decision = (
                            dst_gs_node_id,
                            num_isls_per_sat[dst_sat] + gid_to_sat_gsl_if_idx[dst_gid],
                            0
                        )

                # In any case, save the distance of the satellite to the ground station to re-use
                # when we calculate ground station to ground station forwarding
                dist_satellite_to_ground_station[(curr, dst_gs_node_id)] = distance_to_ground_station_m

                # Write to forwarding state
                if not prev_fstate or prev_fstate[(curr, dst_gs_node_id)] != next_hop_decision:
                    f_out.write("%d,%d,%d,%d,%d\n" % (
                        curr,
                        dst_gs_node_id,
                        next_hop_decision[0],
                        next_hop_decision[1],
                        next_hop_decision[2]
                    ))
                fstate[(curr, dst_gs_node_id)] = next_hop_decision

        # Ground stations to ground stations
        # Choose the source satellite which promises the shortest path
        for src_gid in range(num_ground_stations):
            for dst_gid in range(num_ground_stations):
                if src_gid != dst_gid:
                    src_gs_node_id = num_satellites + src_gid
                    dst_gs_node_id = num_satellites + dst_gid

                    # Among the satellites in range of the source ground station,
                    # find the one which promises the shortest distance
                    possible_src_sats = ground_station_satellites_in_range_candidates[src_gid]
                    possibilities = []
                    for a in possible_src_sats:
                        best_distance_offered_m = dist_satellite_to_ground_station[(a[1], dst_gs_node_id)]
                        if not math.isinf(best_distance_offered_m):
                            possibilities.append(
                                (
                                    a[0] + best_distance_offered_m,
                                    a[1]
                                )
                            )
                    #possibilities = sorted(possibilities)
                    #src station must connect to the nearest satellite
                    possibilities = sorted(possible_src_sats)

                    # By default, if there is no satellite in range for one of the
                    # ground stations, it will be dropped (indicated by -1)
                    next_hop_decision = (-1, -1, -1)
                    if len(possibilities) > 0:
                        src_sat_id = possibilities[0][1]
                        next_hop_decision = (
                            src_sat_id,
                            0,
                            num_isls_per_sat[src_sat_id] + gid_to_sat_gsl_if_idx[src_gid]
                        )

                    # Update forwarding state
                    if not prev_fstate or prev_fstate[(src_gs_node_id, dst_gs_node_id)] != next_hop_decision:
                        f_out.write("%d,%d,%d,%d,%d\n" % (
                            src_gs_node_id,
                            dst_gs_node_id,
                            next_hop_decision[0],
                            next_hop_decision[1],
                            next_hop_decision[2]
                        ))
                    fstate[(src_gs_node_id, dst_gs_node_id)] = next_hop_decision
    if is_last:
        with open(output_filename+".temp", "w+") as f_out:
            f_out.write(str(fstate))
    # Finally return result
    return fstate

def calculate_fstate_shortest_path_without_gs_relaying2(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph_only_satellites_with_isls,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        ground_station_satellites_in_range_candidates,
        sat_neighbor_to_if,
        prev_fstate,
        enable_verbose_logs,
        is_last,
        version
):
    #get the commodity list

    with open("commodites.temp","r") as fcomm:
        commodity_list=eval(fcomm.read())
        if enable_verbose_logs:
            print('lecture commodites') 
    with open("debitISL.temp","r") as fISL:
        debitISL=eval(fISL.readline())
        if enable_verbose_logs:
            print("debit lien ISL:",debitISL,"Mb/s")
    # Calculate shortest path distances
    if enable_verbose_logs:
        print("  > Calculating mcnf for graph without ground-station relays")
    # (Note: Numpy has a deprecation warning here because of how networkx uses matrices)
    total_net_graph=sat_net_graph_only_satellites_with_isls.copy()
    #add ground stations to graph
    total_net_graph.add_nodes_from([num_satellites + dst_gid for dst_gid in range(num_ground_stations)])
    #add possible edges to the graph. 

    # TODO /!\
    # the ground station can only be connected to one satellite. 
    # This will not be a problem here because a ground station only communicates with only one other station.
    # /!\ 
    for groundStationId in range(num_ground_stations):
        if ground_station_satellites_in_range_candidates[groundStationId]:
            distanceSatGS,satid = sorted(ground_station_satellites_in_range_candidates[groundStationId])[0]
            total_net_graph.add_edge(satid, num_satellites+groundStationId, weight = distanceSatGS)
        #for distanceSatGS,satid in sorted(ground_station_satellites_in_range_candidates[groundStationId]):
        #	total_net_graph.add_edge(satid, num_satellites+groundStationId, weight = 10000000)#distanceSatGS

    #compute optimal path
    if version=='a':
        list_paths = calcul_paths(total_net_graph, prev_fstate, commodity_list, debitISL, "SRR_arc_node_one_timestep")
    elif version=='b':
        list_paths = calcul_paths(total_net_graph, prev_fstate, commodity_list, debitISL, "SRR_arc_node_one_timestep_shorter")
    elif version=='c':
        list_paths = calcul_paths(total_net_graph, prev_fstate, commodity_list, debitISL, "SRR_arc_node_one_timestep_shorterc")
    elif version=='d':
        list_paths = calcul_paths(total_net_graph, prev_fstate, commodity_list, debitISL, "SRR_arc_node_one_timestep_shorterd")
    elif version=='e':
        list_paths = calcul_paths(total_net_graph, prev_fstate, commodity_list, debitISL, "SRR_arc_node_one_timestep_shortere")
    else:
        raise Exception("Erreur de version d'algorithme")
    # Forwarding state : by default, interfaces down and empty routing table
    if prev_fstate:
        fstate=prev_fstate.copy()
    else:
        fstate = {(cur,dst):(-1,-1,-1) for cur in range(num_satellites+num_ground_stations) for dst in range(num_satellites,num_satellites+num_ground_stations) if cur !=dst}

    # Now write state to file for complete graph
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    if enable_verbose_logs:
        print("  > Writing forwarding state to: " + output_filename)
    
    for i,path in enumerate(list_paths):
            if path:
                #src ground station to first sat
                src_id = path[0]
                dst_gs_node_id = path[-1]
                next_hop_decision=(path[1], 0, num_isls_per_sat[path[1]] + gid_to_sat_gsl_if_idx[src_id-num_satellites])
                fstate[(src_id, dst_gs_node_id)] = next_hop_decision
                
                #last sat to dst ground station
                next_hop_decision = (dst_gs_node_id,num_isls_per_sat[path[-2]] + gid_to_sat_gsl_if_idx[dst_gs_node_id-num_satellites],0)
                fstate[(path[-2], dst_gs_node_id)] = next_hop_decision
                
                #interfaces between satellites
                for k in range(1,len(path)-2):
                    curr,neighbor_id=path[k],path[k+1]
                    next_hop_decision = (neighbor_id,sat_neighbor_to_if[(curr, neighbor_id)],sat_neighbor_to_if[(neighbor_id, curr)])
                    fstate[(curr, dst_gs_node_id)] = next_hop_decision
    
    with open(output_filename, "w+") as f_out:
        for cle in fstate:
            if not prev_fstate or cle not in prev_fstate or prev_fstate[cle] != fstate[cle]:
                    f_out.write("{},{},{},{},{}\n".format(*cle, *fstate[cle]))
                    
    if is_last:
        with open(output_filename+".temp", "w+") as f_out:
            f_out.write(str(fstate))
            
    # Finally return result
    return fstate

def calculate_fstate_shortest_path_with_gs_relaying(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        sat_neighbor_to_if,
        prev_fstate,
        enable_verbose_logs
):

    # Calculate shortest paths
    if enable_verbose_logs:
        print("  > Calculating Floyd-Warshall for graph including ground-station relays")
    # (Note: Numpy has a deprecation warning here because of how networkx uses matrices)
    dist_sat_net = nx.floyd_warshall_numpy(sat_net_graph)

    # Forwarding state
    fstate = {}

    # Now write state to file for complete graph
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    if enable_verbose_logs:
        print("  > Writing forwarding state to: " + output_filename)
    with open(output_filename, "w+") as f_out:

        # Satellites and ground stations to ground stations
        for current_node_id in range(num_satellites + num_ground_stations):
            for dst_gid in range(num_ground_stations):
                dst_gs_node_id = num_satellites + dst_gid

                # Cannot forward to itself
                if current_node_id != dst_gs_node_id:

                    # Among its neighbors, find the one which promises the
                    # lowest distance to reach the destination satellite
                    next_hop_decision = (-1, -1, -1)
                    best_distance_m = 1000000000000000
                    for neighbor_id in sat_net_graph.neighbors(current_node_id):

                        # Any neighbor must be reachable
                        if math.isinf(dist_sat_net[(current_node_id, neighbor_id)]):
                            raise ValueError("Neighbor cannot be unreachable")

                        # Calculate distance = next-hop + distance the next hop node promises
                        distance_m = (
                            sat_net_graph.edges[(current_node_id, neighbor_id)]["weight"]
                            +
                            dist_sat_net[(neighbor_id, dst_gs_node_id)]
                        )
                        if (
                                not math.isinf(dist_sat_net[(neighbor_id, dst_gs_node_id)])
                                and
                                distance_m < best_distance_m
                        ):

                            # Check node identifiers to determine what are the
                            # correct interface identifiers
                            if current_node_id >= num_satellites and neighbor_id < num_satellites:  # GS to sat.
                                my_if = 0
                                next_hop_if = (
                                    num_isls_per_sat[neighbor_id]
                                    +
                                    gid_to_sat_gsl_if_idx[current_node_id - num_satellites]
                                )

                            elif current_node_id < num_satellites and neighbor_id >= num_satellites:  # Sat. to GS
                                my_if = (
                                    num_isls_per_sat[current_node_id]
                                    +
                                    gid_to_sat_gsl_if_idx[neighbor_id - num_satellites]
                                )
                                next_hop_if = 0

                            elif current_node_id < num_satellites and neighbor_id < num_satellites:  # Sat. to sat.
                                my_if = sat_neighbor_to_if[(current_node_id, neighbor_id)]
                                next_hop_if = sat_neighbor_to_if[(neighbor_id, current_node_id)]

                            else:  # GS to GS
                                raise ValueError("GS-to-GS link cannot exist")

                            # Write the next-hop decision
                            next_hop_decision = (
                                neighbor_id,  # Next-hop node identifier
                                my_if,        # My outgoing interface id
                                next_hop_if   # Next-hop incoming interface id
                            )

                            # Update best distance found
                            best_distance_m = distance_m

                    # Write to forwarding state
                    if not prev_fstate or prev_fstate[(current_node_id, dst_gs_node_id)] != next_hop_decision:
                        f_out.write("%d,%d,%d,%d,%d\n" % (
                            current_node_id,
                            dst_gs_node_id,
                            next_hop_decision[0],
                            next_hop_decision[1],
                            next_hop_decision[2]
                        ))
                    fstate[(current_node_id, dst_gs_node_id)] = next_hop_decision

    # Finally return result
    return fstate
