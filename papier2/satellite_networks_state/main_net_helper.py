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

import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../satgenpy"))
import satgen
import math
import yaml

from .input_data.constants import *

class MainNetHelper:

    def __init__(
            self, dico_config, constellation_config_file, 
    output_generated_data_dir # Final directory in which the result will be placed
    ):

        self.config=dico_config
        self.output_generated_data_dir = output_generated_data_dir

        with open(constellation_config_file, 'r') as f:
            cstl_dico=yaml.load(f, Loader=yaml.Loader)
        
        self.cstl_config=cstl_dico
        
        altitude = cstl_dico['ALTITUDE_M']
        
        self.MEAN_MOTION_REV_PER_DAY = SECONDS_SIDEREAL_DAY*math.sqrt(MU_EARTH/(altitude+EARTH_RADIUS)**3)/math.pi/2  # ~14.5 revs/jour
        

        self.NUM_ORBS = cstl_dico['NUM_ORBS']
        self.NUM_SATS_PER_ORB = cstl_dico['NUM_SATS_PER_ORB']
        self.cstl_config['satellite'] = {"nombre": self.NUM_ORBS * self.NUM_SATS_PER_ORB}
        self.cstl_config['NB_SATS'] = self.NUM_ORBS * self.NUM_SATS_PER_ORB #TODO remove this stupidity
        self.INCLINATION_DEGREE = cstl_dico['INCLINATION_DEGREE']

        self.dict_type_ivl={"satellite": range(self.cstl_config["satellite"]['nombre'])}
        prec=self.cstl_config["satellite"]['nombre']
        for obj in self.cstl_config["TYPES_OBJETS_SOL"]:
            self.dict_type_ivl[obj]=range(prec, prec+self.cstl_config[obj]["nombre"])
            prec+=self.cstl_config[obj]["nombre"]

    def init_ground_stations(self):
        # Add base name to setting
        name = self.cstl_config['BASE_NAME'] + "_" + self.config['isls'] + "_" + self.config['algo']

        # Create output directories
        if not os.path.isdir(self.output_generated_data_dir):
            os.makedirs(self.output_generated_data_dir, exist_ok=True)
        if not os.path.isdir(self.output_generated_data_dir + "/" + name):
            os.makedirs(self.output_generated_data_dir + "/" + name, exist_ok=True)

        # Ground stations
        print("Generating ground stations...")
        # create a from_to list
        return satgen.extend_ground_objects(self.config['graine'], self.cstl_config, self.output_generated_data_dir + "/" + name + "/ground_stations.txt")

    def calculate(self):
        # This function generates network links and compute interfaces

        # Add base name to setting
        name = self.cstl_config['BASE_NAME'] + "_" + self.config['isls'] + "_" + self.config['algo']

        # TLEs
        print("Generating TLEs...")
        satgen.generate_tles_from_scratch_manual(
            self.output_generated_data_dir + "/" + name + "/tles.txt",
            self.cstl_config['NICE_NAME'],
            self.NUM_ORBS,
            self.NUM_SATS_PER_ORB,
            self.cstl_config['PHASE_DIFF'],
            self.INCLINATION_DEGREE,
            self.cstl_config['ECCENTRICITY'],
            self.cstl_config['ARG_OF_PERIGEE_DEGREE'],
            self.MEAN_MOTION_REV_PER_DAY
        )

        #generate links. These will be used for interface generation separately for ns3 and python route script.
        #Therefore order is very important
        total_nb_devsol=sum(self.cstl_config[obj]['nombre'] for obj in self.cstl_config['TYPES_OBJETS_SOL'])
        network_links={}
        interfaces={}
        interfaces_number={i:0 for i in range(self.cstl_config['NB_SATS']+total_nb_devsol)}# device:next_nb_of_interface
        interfaces_number_cpy=interfaces_number.copy()
        gsl_devs=set()
        for i,lien in enumerate(self.cstl_config['LINKS']):
            type_lien, objets, proprietes_lien= lien
            nom_lien=f"lix{i}"
            if type_lien=='isl':
                assert list(objets.keys())==["satellite"]
                network_links[nom_lien], nvelles_interfaces=generate_plus_grid_isls(
                    os.path.join(self.output_generated_data_dir, name, nom_lien+".txt"),
                    self.NUM_ORBS,
                    self.NUM_SATS_PER_ORB,
                    interfaces_number,
                    isl_shift=0
                )
                interfaces.update(nvelles_interfaces)
                if proprietes_lien.get("limiteDist", False):
                    self.cstl_config['LINKS'][i][2]["max_length_m"]={}
                    self.cstl_config['LINKS'][i][2]["polar_desactivation_anomaly_degree"]={}
                    for obj in objets:
                        # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
                        self.cstl_config['LINKS'][i][2]["max_length_m"][obj]=2 * math.sqrt(math.pow(EARTH_RADIUS + self.cstl_config['ALTITUDE_M'], 2) - math.pow(EARTH_RADIUS + 80000, 2))
                        self.cstl_config['LINKS'][i][2]["polar_desactivation_anomaly_degree"][obj] = self.cstl_config['ISL_POLAR_DESACTIVATION_ANOMALY_DEGREE']


            elif type_lien=='gsl':
                #network_links will change with time, but interface number remain the same
                network_links[nom_lien]=None
                interfaces.update(generate_gsl_interfaces(nom_lien, interfaces_number, *[self.dict_type_ivl[obj] for obj in objets]))
                for obj in objets:
                    gsl_devs.add(obj)
                
                if proprietes_lien.get("limiteDist", False):
                    self.cstl_config['LINKS'][i][2]["max_length_m"]={}
                    for obj in objets:
                        elev=self.cstl_config[obj].get('minElevation', False)
                        if elev:
                            t=EARTH_RADIUS*math.sin(math.radians(elev))
                            max_gsl_m=(math.sqrt((EARTH_RADIUS+self.cstl_config['ALTITUDE_M'])**2-EARTH_RADIUS**2+t**2) -t)*self.cstl_config["RADIO_K_FACTOR"]
                            self.cstl_config['LINKS'][i][2]["max_length_m"][obj]=max_gsl_m


            elif type_lien=='tl':
                network_links[nom_lien], nvelles_interfaces=generate_tl_net(
                    os.path.join(self.output_generated_data_dir, name, nom_lien+".txt"),
                    interfaces_number,
                    *[self.dict_type_ivl[obj] for obj in objets]
                )
                interfaces.update(nvelles_interfaces)

            else:
                raise Exception("type de lien non reconnu")
            
            res= (interfaces_number_cpy == interfaces_number)
            print(f"succes ajout d'interfaces: {res}")
        
        # Forwarding state, handle special GSL case
        net_gen_infos={}
        net_gen_infos['endpoints'] = self.cstl_config['ENDPOINTS']
        net_gen_infos['dev gsl'] = gsl_devs
        net_gen_infos['interfaces'] = interfaces
        net_gen_infos['network links'] = network_links
        net_gen_infos['dev ranges'] = self.dict_type_ivl
        net_gen_infos['liste liens'] = self.cstl_config['LINKS']


        print("Generating forwarding state...")
        satgen.help_dynamic_state(
            self.output_generated_data_dir,
            self.config['threads'],  # Number of threads
            name,
            self.config['pas'],
            self.config['duree'],
            self.config['algo'],
            net_gen_infos
        )

def generate_plus_grid_isls(output_filename_isls, n_orbits, n_sats_per_orbit, interfaces_number, isl_shift):
    """
    Generate plus grid ISL file.

    :param output_filename_isls     Output filename
    :param n_orbits:                Number of orbits
    :param n_sats_per_orbit:        Number of satellites per orbit
    :param isl_shift:               ISL shift between orbits (e.g., if satellite id in orbit is X,
                                    does it also connect to the satellite at X in the adjacent orbit)
    :param idx_offset:              Index offset (e.g., if you have multiple shells)
    """

    if n_orbits < 3 or n_sats_per_orbit < 3:
        raise ValueError("Number of x and y must each be at least 3")
    
    nvelles_interfaces={}
    list_isls = []
    for i in range(n_orbits):
        for j in range(n_sats_per_orbit):
            sat = i * n_sats_per_orbit + j

            # Link to the next in the orbit
            sat_same_orbit = i * n_sats_per_orbit + ((j + 1) % n_sats_per_orbit)
            sat_adjacent_orbit = ((i + 1) % n_orbits) * n_sats_per_orbit + ((j + isl_shift) % n_sats_per_orbit)

            # Same orbit
            list_isls.append((sat, sat_same_orbit, 's'))
            nvelles_interfaces[(sat, sat_same_orbit)] = interfaces_number[sat]
            nvelles_interfaces[(sat_same_orbit, sat)] = interfaces_number[sat_same_orbit]
            interfaces_number[sat] += 1
            interfaces_number[sat_same_orbit] += 1

            # Adjacent orbit
            list_isls.append((sat, sat_adjacent_orbit, 'a'))
            nvelles_interfaces[(sat, sat_adjacent_orbit)] = interfaces_number[sat]
            nvelles_interfaces[(sat_adjacent_orbit, sat)] = interfaces_number[sat_adjacent_orbit]
            interfaces_number[sat] += 1
            interfaces_number[sat_adjacent_orbit] += 1
    
    with open(output_filename_isls, 'w') as f:
        for (a, b, val) in list_isls:
            f.write(str(a) + " " + str(b) + " " + str(val) + "\n")

    return list_isls, nvelles_interfaces

def generate_tl_net(output_filename_tls, interfaces_number, objetsA, objetsB):
    """
    Generate plus grid ISL file.

    :param output_filename_isls     Output filename
    :param interfaces_number        dictionary containing the next interface number

    """
    
    nvelles_interfaces={}
    liste_liens = []
    if len(objetsB)!=len(objetsA):
        raise Exception("erreur TL: il doit y avoir bijection entre les objets A et B")
    delta=min(objetsA)-min(objetsB)
    for a in objetsA:
        b=a-delta
        
        liste_liens.append((a, b))

        nvelles_interfaces[(a, b)] = interfaces_number[a]
        nvelles_interfaces[(b, a)] = interfaces_number[b]
        interfaces_number[a] += 1
        interfaces_number[b] += 1
    
    with open(output_filename_tls, 'w') as f:
        for (a, b) in liste_liens:
            f.write(f"{a},{b}\n")

    return liste_liens, nvelles_interfaces

def generate_gsl_interfaces(nom_lien, interfaces_number, *objets):
    nvelles_interfaces={}
    for rnge_objet in objets:
        for i in rnge_objet:
            nvelles_interfaces[(i, nom_lien)] = interfaces_number[i]
            interfaces_number[i]+=1
    return nvelles_interfaces