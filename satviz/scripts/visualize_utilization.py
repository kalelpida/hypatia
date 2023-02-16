# MIT License
#
# Copyright (c) 2020 Debopam Bhattacherjee
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

import math
import ephem
import pandas as pd
import re, os
import yaml

try:
    from . import util
except (ImportError, SystemError):
    import util

import sys


IN_UTIL_DIR='../../papier2/sauvegardes/test'
MODE = 2 #0: "S->UE", 1: "UE->S" 2:"TOUS"
# Time in ms for which visualization will be generated
GEN_TIME = 3000  #ms
UTIL_INTERVAL = 100


# For all end-end paths, visualize link utilization at a specific time instance

EARTH_RADIUS = 6378135.0 # WGS72 value; taken from https://geographiclib.sourceforge.io/html/NET/NETGeographicLib_8h_source.html
MU_EARTH= 3.98574405e+14
SECONDS_SIDEREAL_DAY= 86164

# CONSTELLATION GENERATION GENERAL CONSTANTS
PHASE_DIFF = True
INITIAL_EPOCH = "2000-01-01 00:00:00"

#Default constellation
NAME='tas_700'
ECCENTRICITY=1e-7
ARG_OF_PERIGEE_DEGREE=0.0
ALTITUDE_M=700000
NUM_ORBS=28
NUM_SATS_PER_ORB=27
INCLINATION_DEGREE=65
NUM_STATIONS=10
TOTAL_NUM_SATS=NUM_ORBS*NUM_ORBS
EPOCH = (pd.to_datetime(INITIAL_EPOCH) + pd.to_timedelta(GEN_TIME, unit='ms')).strftime(
        format='%Y/%m/%d %H:%M:%S.%f')

iterator=iter([0]) # to assert constellation parameters won't change between experiments
def maj_cstl(**kwargs):
    global MEAN_MOTION_REV_PER_DAY, NUM_STATIONS
    changement=False
    for k, v in kwargs.items():
        if k in globals():
            if globals()[k]!=v:
                changement=True
                globals()[k]=v
    if 'gateway' in kwargs:
        if NUM_STATIONS != kwargs['gateway']['nombre']:
                changement=True
                NUM_STATIONS = kwargs['gateway']['nombre']
    if changement:
        next(iterator)
    MEAN_MOTION_REV_PER_DAY = SECONDS_SIDEREAL_DAY*math.sqrt(MU_EARTH/(ALTITUDE_M+EARTH_RADIUS)**3)/math.pi/2


# General files needed to generate visualizations; Do not change for different simulations
topFile = "../static_html/top.html"
bottomFile = "../static_html/bottom.html"


# Input file; Generated during simulation
# Note the file_name consists of the 2 city IDs being offset by the size of the constellation
# City and user IDs are available in the cities_and_users_detail_file.
# If city ID is X (for Paris X = 24) and constellation is Starlink_550 (1584 satellites),
# then offset ID is 1584 + 24 = 1608.
CITIES_AND_USERS_DETAIL_FILE="" # ground_stations.txt
IN_UTIL_FILE = "" # link.tx

tous_objs = []
city_details = {}
paths_over_time = []


# Output directory for creating visualization html files
OUT_DIR = "../viz_output/"
if len(sys.argv)>1:
    IN_UTIL_DIR = sys.argv[1]


tous_objs = []
time_wise_util = {}
liste_commodites=[]

def add_dico(*args,dico={}):
    n=len(args)
    assert n>=2
    dic=dico
    for k in range(n-2):
        if args[k] not in dic:
            dic[args[k]]={}
        dic=dic[args[k]]
    if args[n-2] not in dic:
        dic[args[n-2]]=[]
    dic[args[n-2]].append(args[-1])

def parse_commodites(fic):
    pass

def retrouveFicsEtConfigRecursif(chemin_initial):
    trouves={} # nom: [gs.txt, link.tx]
    aChercher=[chemin_initial]
    while aChercher:
        nom=aChercher.pop()
        for glob in os.listdir(nom):
            x=os.path.join(nom,glob)  
            if os.path.isdir(x):
                aChercher.append(x)
            elif glob=="courante.yaml":
                #update constellation parameters 
                with open(x, 'r') as f:
                    dico_params=yaml.load(f, Loader=yaml.Loader)
                constel_fic=dico_params.get('constellation')
                constel_fic="../../papier2/config/"+constel_fic+".yaml"
                with open(constel_fic, 'r') as f:
                    dico_constel=yaml.load(f, Loader=yaml.Loader)
                maj_cstl(**dico_constel)
            elif glob=="link.tx":
                svgde=re.search('svgde_[^/]*20\d{2}-\d{2}-\d{2}-\d{4}_\d+',nom).group(0)
                add_dico(svgde, x, dico=trouves)
            elif glob=="ground_stations.txt":
                svgde=re.search('svgde_[^/]*20\d{2}-\d{2}-\d{2}-\d{4}_\d+',nom).group(0)
                add_dico(svgde, x, dico=trouves)
    return trouves

def generate_link_util_at_time():
    """
    Generates link utilization for the network at specified time
    :return: HTML formatted string for visualization
    """
    viz_string = ""
    global time_wise_util
    dico_links={}
    dico_links_src_gsl={} #list each gsl interface destinations # suppose these destinations won't vary in UTIL_INTERVAL (no routing table update)
    gen_time_ns=int(GEN_TIME)*int(1e6)
    fin_interval_ns=gen_time_ns+int(UTIL_INTERVAL)*int(1e6)
    with open(IN_UTIL_FILE, 'r') as f:
        while (l:=f.readline()):
            #30000,767,431,2,0,1502,1201599,GSL-tx
            deb, fin =l.find(','), l.rfind(',')
            if (t_ns:=int(l[:deb])) < gen_time_ns:
                continue
            elif t_ns> fin_interval_ns:
                break
            type_lien=l[fin+1:].strip()
            src, dst, idcom, _, _, txtime_ns = eval(l[deb+1:fin])
            if idcom%2==MODE:
                continue
            txtime_ns=min(txtime_ns,fin_interval_ns-t_ns)
            assert txtime_ns > 0
            #bandwidth is shared in emission for gs links
            if type_lien.startswith("GSL"):
                if src in dico_links_src_gsl:
                    util_actuelle=max([dico_links[(src, unedst)] for unedst in dico_links_src_gsl[src]])
                    dico_links_src_gsl[src].add(dst)
                    for unedst in dico_links_src_gsl[src]-{dst}:
                        dico_links[(src, unedst)]=util_actuelle + txtime_ns*1e-6/UTIL_INTERVAL
                    dico_links[(src, dst)]=util_actuelle # will be incremented just after
                else:
                    dico_links_src_gsl[src]={dst}
            if (src, dst) in dico_links:
                dico_links[(src, dst)]+=txtime_ns*1e-6/UTIL_INTERVAL
            else:
                dico_links[(src, dst)]=txtime_ns*1e-6/UTIL_INTERVAL
    for obj in tous_objs:
        match obj['type']:
            case 'sat':
                material="Cesium.Color.BLACK.withAlpha(1)"
                dimensions=(10000.0, 10000.0, 10000.0)
            case 'gateway':
                material="Cesium.Color.ROYALBLUE.withAlpha(1)"
                dimensions=(60000.0, 60000.0, 60000.0)
            case 'ue':
                material="Cesium.Color.SIENNA.withAlpha(1)"
                dimensions=(30000.0, 30000.0, 30000.0)
            case _:
                raise Exception('type non reconnu')
        viz_string += "var redSphere = viewer.entities.add({name : '', position: Cesium.Cartesian3.fromDegrees(" \
                      + str(obj["lon"]) + "," \
                      + str(obj["lat"]) + "," \
                      + str(obj["alt_m"]) + "), " \
                      + "ellipsoid : {radii : new Cesium.Cartesian3"+ str(dimensions)+", " \
                      + "material : "+material+",}});\n"

    deja_vu=set()
    for (src, dst),val in dico_links.items():
        cletriee=min(src, dst), max(src, dst)
        if cletriee in deja_vu:
            continue

        deja_vu.add(cletriee)
        if (dst, src) in dico_links: 
            utilization=max(val, dico_links[(dst, src)])
        else:
            utilization=val
        if utilization>1:
            raise Exception("utilisation supérieure à ressources disponibles")
        
        link_width = 0.1 + 5 * utilization
        if utilization >= 0.5:
            red_weight = 255
            green_weight = 0 + round(255 * (1 - utilization) / 0.5)
        else:
            green_weight = 255
            red_weight = 255 - round(255 * (0.5 - utilization) / 0.5)
        hex_col = '%02x%02x%02x' % (red_weight, green_weight, 0)
        #print(sat1, sat2, utilization, hex_col)
        viz_string += "viewer.entities.add({name : '', polyline: { positions: Cesium.Cartesian3.fromDegreesArrayHeights([" \
                        + str(tous_objs[src]["lon"]) + "," \
                        + str(tous_objs[src]["lat"]) + "," \
                        + str(tous_objs[src]["alt_m"]) + "," \
                        + str(tous_objs[dst]["lon"]) + "," \
                        + str(tous_objs[dst]["lat"]) + "," \
                        + str(tous_objs[dst]["alt_m"]) + "]), " \
                        + "width: "+str(link_width)+", arcType: Cesium.ArcType.NONE, " \
                        + "material: new Cesium.PolylineOutlineMaterialProperty({ " \
                        + "color: Cesium.Color.fromCssColorString('#"+str(hex_col)+"'), outlineWidth: 0, outlineColor: Cesium.Color.BLACK})}});"
    return viz_string
       
tous_objs=[]
if __name__ == "__main__":
    trouves=retrouveFicsEtConfigRecursif(IN_UTIL_DIR)

    sat_objs = util.generate_sat_obj_position_list(
        NUM_ORBS,
        NUM_SATS_PER_ORB,
        INITIAL_EPOCH,
        PHASE_DIFF,
        INCLINATION_DEGREE,
        ECCENTRICITY,
        ARG_OF_PERIGEE_DEGREE,
        MEAN_MOTION_REV_PER_DAY,
        ALTITUDE_M,
        EPOCH
    ) 
    for svgde, (CITIES_AND_USERS_DETAIL_FILE, IN_UTIL_FILE) in trouves.items():
        tous_objs = sat_objs + util.generate_sol_obj_position_list(CITIES_AND_USERS_DETAIL_FILE)
        viz_string = generate_link_util_at_time()
        OUT_HTML_FILE = f"{OUT_DIR}{NAME}_util_{MODE}{svgde}.html"
        util.write_viz_files(viz_string, topFile, bottomFile, OUT_HTML_FILE)
