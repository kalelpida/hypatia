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
import os


def extend_ground_stations(filename_ground_stations_basic_in, filename_ground_stations_out):
    ground_stations = read_ground_stations_basic(filename_ground_stations_basic_in)
    with open(filename_ground_stations_out, "w+") as f_out:
        for ground_station in ground_stations:
            cartesian = geodetic2cartesian(
                float(ground_station["latitude_degrees"]),
                float(ground_station["longitude_degrees"]),
                float(ground_station["elevation_m"])
            )
            f_out.write(
                "%d,%s,%f,%f,%f,%f,%f,%f,station\n" % (
                    ground_station["gid"],
                    ground_station["name"],
                    float(ground_station["latitude_degrees"]),
                    float(ground_station["longitude_degrees"]),
                    float(ground_station["elevation_m"]),
                    cartesian[0],
                    cartesian[1],
                    cartesian[2]
                )
            )
    

def extend_ground_objects(graine, cstl_config, filename_ground_out):
    # first, generate position file
    np.random.seed(graine)
    if len(cstl_config.get('ENDPOINTS', []))==0:
        raise Exception("choisir les terminaux à l'origine des flux: ENDPOINTS doit contenir 1 ou 2 type d'objets.")

    selection_positions_sol={}
    ground_object_positions=[]
    for objet_sol in cstl_config['TYPES_OBJETS_SOL']:
        positions = cstl_config[objet_sol]['positions']
        if not os.path.isfile(nomfic:="input_data/{}.txt".format(positions)):
            assert os.path.isfile(nomfic:="input_data/{}.csv".format(positions))
        liste_positions_sol=read_ground_stations_basic(nomfic)

        if cstl_config[objet_sol]["nombre"] > len(liste_positions_sol):
            raise Exception('please, generate more positions. For UEs, this can be done using `generate_users.py` in satellite_networks_state/input_data/')
        liste_positions_sol=liste_positions_sol[:cstl_config[objet_sol]["nombre"]]

        decalage_id_sol=len(ground_object_positions)
        selection_positions_sol[objet_sol] = liste_positions_sol
        for ids, position in enumerate(liste_positions_sol):
            cartesian = geodetic2cartesian(
            float(position["latitude_degrees"]),
            float(position["longitude_degrees"]),
            float(position["elevation_m"])
            )
            ground_object_positions.append(
                "%d,%s,%f,%f,%f,%f,%f,%f,%s\n" % (
                    ids+decalage_id_sol,
                    position["name"],
                    float(position["latitude_degrees"]),
                    float(position["longitude_degrees"]),
                    float(position["elevation_m"]),
                    cartesian[0],
                    cartesian[1],
                    cartesian[2],
                    objet_sol
                )
            )
    #save config
    with open(filename_ground_out, "w+") as f_out:
        f_out.writelines(ground_object_positions)
    
    #Then propose flow lines
    list_from_to=[]
    #premier cas, 1 seule classe de terminaux. Ceux-ci s'échangent des informations entre eux, 2 par 2.
    if len(cstl_config['ENDPOINTS'])==1:
        nom_obj=cstl_config['ENDPOINTS'][0]
        decalage=cstl_config['NB_SATS']
        for obj in cstl_config['TYPES_OBJETS_SOL']:
            if obj==nom_obj:
                break
            decalage+=cstl_config[obj]["nombre"]
        nb=cstl_config[nom_obj]["nombre"]
        liste_paires= np.random.choice(nb, size=(nb//2, 2), replace=False)
        for (src, dst) in liste_paires:
            list_from_to.append([src+decalage, dst+decalage])
            list_from_to.append([dst+decalage, src+decalage])
        return list_from_to

    #second cas, 2 classes de terminaux.
    # Les objets de la première classe vont tous établir 2 flux (1 aller, 1 retour) vers des objets de la seconde classe.
    # Dans la plupart des cas, le correspondant est le plus proche
    types_client, type_serveur=cstl_config['ENDPOINTS'][:-1], cstl_config['ENDPOINTS'][-1]
    nbserveurs=cstl_config[type_serveur]["nombre"]
    decalages={}
    # id attribution begins with satellites, then follows TYPE_OBJET_SOL order
    for nom_obj in cstl_config['ENDPOINTS']:
        decalage=cstl_config['NB_SATS']
        for obj in cstl_config['TYPES_OBJETS_SOL']:
            if obj==nom_obj:
                break
            decalage+=cstl_config[obj]["nombre"]
        decalages[nom_obj]=decalage
    
    for type_client in types_client:
        nb=cstl_config[type_client]["nombre"]
        for pos_client in selection_positions_sol[type_client]:
            id_client = int(pos_client['gid'])
            # add source and dest of commodities 
            if id_client < 0.2*nb:#20% flots longs
                id_serveur=np.random.randint(0, nbserveurs)
            else: #80% flots courts
                id_serveur=sorted([(geodesic_distance_m_between_ground_stations(pos_client, pos_serveur), int(pos_serveur['gid'])) for pos_serveur in selection_positions_sol[type_serveur]])[0][1]

            # remember that for convenience in later routing, IDs in commodities are allocated from 0 to infinite
            list_from_to.append([id_client+decalages[type_client], id_serveur+decalages[type_serveur]])
            list_from_to.append([id_serveur+decalages[type_serveur], id_client+decalages[type_client]])
    return list_from_to