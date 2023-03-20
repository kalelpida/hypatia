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
from .read_ground_stations import *
import numpy as np


def extend_ground_stations(filename_ground_stations_basic_in, filename_ground_stations_out):
    ground_stations = read_ground_stations_basic(filename_ground_stations_basic_in)
    with open(filename_ground_stations_out, "w+") as f_out:
        for ground_station in ground_stations:
            cartesian = geodetic2cartesian(
                float(ground_station["latitude_degrees_str"]),
                float(ground_station["longitude_degrees_str"]),
                ground_station["elevation_m_float"]
            )
            f_out.write(
                "%d,%s,%f,%f,%f,%f,%f,%f,station\n" % (
                    ground_station["gid"],
                    ground_station["name"],
                    float(ground_station["latitude_degrees_str"]),
                    float(ground_station["longitude_degrees_str"]),
                    ground_station["elevation_m_float"],
                    cartesian[0],
                    cartesian[1],
                    cartesian[2]
                )
            )

def extend_stations(graine, NbUEs, cstl_config, filename_ground_stations_out):
    np.random.seed(graine)
    if cstl_config['gateway']['type'] == 'topCitiesHypatia':
        ues = read_ground_stations_basic("input_data/ground_stations_cities_sorted_by_estimated_2025_pop_top_100.basic.txt")
    elif cstl_config['gateway']['type'] == 'topCitiesUN':
        ues = read_ground_stations_basic("input_data/ground_stations_cities_by_estimated_2025_pop_300k_UN.csv")
    elif cstl_config['gateway']['type'] == 'Lille':
        ues = read_ground_stations_basic("input_data/ground_stations_Lille.csv")
    else: # autres cas à faire
        ues = read_ground_stations_basic("input_data/UEs_{}.txt".format(cstl_config['ue']['type']))
    with open(filename_ground_stations_out, "w+") as f_out:
        for ground_station in ues[:NbUEs]:
            cartesian = geodetic2cartesian(
                float(ground_station["latitude_degrees_str"]),
                float(ground_station["longitude_degrees_str"]),
                ground_station["elevation_m_float"]
            )
            f_out.write(
                "%d,%s,%f,%f,%f,%f,%f,%f,ue\n" % (
                    ground_station["gid"],
                    ground_station["name"],
                    float(ground_station["latitude_degrees_str"]),
                    float(ground_station["longitude_degrees_str"]),
                    ground_station["elevation_m_float"],
                    cartesian[0],
                    cartesian[1],
                    cartesian[2]
                )
            )
    nbsats=cstl_config['nb_sats']
    liste_paires= np.random.choice(NbUEs, size=(NbUEs//2, 2), replace=False)
    list_from_to=[]
    for (src, dst) in liste_paires:
        list_from_to.append([src+nbsats, dst+nbsats])
        list_from_to.append([dst+nbsats, src+nbsats])
    return list_from_to

def extend_stations_and_users(graine, NbGateways, NbUEs, cstl_config, filename_ground_out):
    np.random.seed(graine)
    #gather ground bodies 
    if cstl_config['gateway']['type'] == 'topCitiesHypatia':
        gateways = read_ground_stations_basic("input_data/ground_stations_cities_sorted_by_estimated_2025_pop_top_100.basic.txt")
    elif cstl_config['gateway']['type'] == 'topCitiesUN':
        gateways = read_ground_stations_basic("input_data/ground_stations_cities_by_estimated_2025_pop_300k_UN.csv")
    elif cstl_config['gateway']['type'] == 'Lille':
        gateways = read_ground_stations_basic("input_data/ground_stations_Lille.csv")
    else: # autres cas à faire
        raise Exception("config not recognised")
    UEs = read_ground_stations_basic("input_data/UEs_{}.txt".format(cstl_config['ue']['type']))
    if NbUEs > len(UEs):
        raise Exception('please, generate more users. This can be done using `generate_users.py` in satellite_networks_state/input_data/')
    
    list_from_to=[]

    #save ground bodies for simulation
    ground_objects_positions=[]
    for gid, ground_station in enumerate(gateways[:NbGateways]):
        cartesian = geodetic2cartesian(
            float(ground_station["latitude_degrees_str"]),
            float(ground_station["longitude_degrees_str"]),
            ground_station["elevation_m_float"]
        )
        ground_objects_positions.append(
            "%d,%s,%f,%f,%f,%f,%f,%f,gateway\n" % (
                gid,
                ground_station["name"],
                float(ground_station["latitude_degrees_str"]),
                float(ground_station["longitude_degrees_str"]),
                ground_station["elevation_m_float"],
                cartesian[0],
                cartesian[1],
                cartesian[2]
            )
        )

    for gid, ground_station in enumerate(UEs[:NbUEs]):
        cartesian = geodetic2cartesian(
            float(ground_station["latitude_degrees_str"]),
            float(ground_station["longitude_degrees_str"]),
            ground_station["elevation_m_float"]
        )
        
        # add source and dest of commodities 
        if gid < 0.2*NbUEs:#20% flots longs
            dest=np.random.randint(0, NbGateways)
        else: #80% flots courts
            dest=sorted([(geodesic_distance_m_between_ground_stations(ground_station, gateway), sid) for sid, gateway in enumerate(gateways[:NbGateways])])[0][1]
        
        gid+=NbGateways
        ground_objects_positions.append(
            "%d,%s,%f,%f,%f,%f,%f,%f,ue\n" % (
                gid,
                ground_station["name"],
                float(ground_station["latitude_degrees_str"]),
                float(ground_station["longitude_degrees_str"]),
                ground_station["elevation_m_float"],
                cartesian[0],
                cartesian[1],
                cartesian[2]
            )
        )

        # remember that for convenience in later routing, IDs in commodities are allocated from 0 to infinite
        # begin by satellites, then ground gateways, finally users
        nbsats=cstl_config['nb_sats']
        list_from_to.append([gid+nbsats, dest+nbsats])
        list_from_to.append([dest+nbsats, gid+nbsats])

    #save config
    with open(filename_ground_out, "w+") as f_out:
        f_out.writelines(ground_objects_positions)
    
    return list_from_to
        