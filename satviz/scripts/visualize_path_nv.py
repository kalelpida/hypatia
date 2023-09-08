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
import sys, os
import re, yaml

try:
    from . import util
except (ImportError, SystemError):
    import util

# Time in ms for which visualization will be generated
GEN_TIMES_ms=[0, 6000, 10000, 14000]  #ms
EXPERIENCE='papaver4/svgde_2023-09-02-1921_2_3978740' #09-07-1834
COMPLEMENT_NOM=''
SRC_DST=[783, 857]



experience_full_path=os.path.join(os.path.dirname(__file__), '../../papier2/sauvegardes',EXPERIENCE)
assert os.path.isdir(experience_full_path)

# General files needed to generate visualizations; Do not change for different simulations
topFile = "../static_html/top.html"
bottomFile = "../static_html/bottom.html"

# Input file; Generated during simulation
for fic in os.scandir(experience_full_path):
    if fic.name.endswith("campagne.yaml"):
        with open(fic.path) as f:
            dico=yaml.load(f, Loader=yaml.Loader)
        duree_simu=dico['duree']
        pas_maj_routage=dico['pas']
        nom_cstl=dico["constellation"]
        nom_campagne=dico['nom_campagne']
        break
else:
    raise Exception("erreur, fichier des paramètres de campagne non trouvé")

city_detail_file = os.path.join(experience_full_path, "ground_stations.txt")
if not os.path.isfile(city_detail_file):
    print("erreur fichier, vérifier le fichier des stations sol")
    exit(0)

# CONSTELLATION GENERATION GENERAL CONSTANTS
for fic in os.scandir(experience_full_path):
    if fic.name.endswith(f"{nom_cstl}.yaml"):
        with open(fic.path) as f:
            dico_cstl=yaml.load(f, Loader=yaml.Loader)
        for nom, val in dico_cstl.items():
            if nom.isupper():
                globals()[nom]=val
        break
else:
    raise Exception("erreur, fichier de constellation non trouvé")

EARTH_RADIUS = 6378135.0 # WGS72 value; taken from https://geographiclib.sourceforge.io/html/NET/NETGeographicLib_8h_source.html
MU_EARTH= 3.98574405e+14
SECONDS_SIDEREAL_DAY= 86164
MEAN_MOTION_REV_PER_DAY = SECONDS_SIDEREAL_DAY*math.sqrt(MU_EARTH/(ALTITUDE_M+EARTH_RADIUS)**3)/math.pi/2
NUM_SATS= NUM_ORBS*NUM_SATS_PER_ORB
EPOCH = "2000-01-01 00:00:00"
sat_objs = util.generate_sat_obj_list(
    NUM_ORBS,
    NUM_SATS_PER_ORB,
    EPOCH,
    PHASE_DIFF,
    INCLINATION_DEGREE,
    ECCENTRICITY,
    ARG_OF_PERIGEE_DEGREE,
    MEAN_MOTION_REV_PER_DAY,
    ALTITUDE_M
)


# Note the file_name consists of the 2 city IDs being offset by the size of the constellation
# City IDs are available in the city_detail_file.
# If city ID is X (for Paris X = 24) and constellation is Starlink_550 (1584 satellites),
# then offset ID is 1584 + 24 = 1608.
city_details = util.read_ground_objects_file(city_detail_file, offset=NUM_SATS)
src_dst_str=str(SRC_DST)

# Output directory for creating visualization html files
OUT_DIR = "../viz_output/"
OUT_HTML_BASE = OUT_DIR + nom_campagne + COMPLEMENT_NOM

def main():
    for instant in GEN_TIMES_ms:
        viz_string = generate_path_at_time(instant)
        out_html_file = OUT_HTML_BASE + "_"+city_details[SRC_DST[0]]["name"] + "_" +city_details[SRC_DST[1]]["name"] + f"_{instant}ms.html"
        util.write_viz_files(viz_string, topFile, bottomFile, out_html_file)

def generate_path_at_time(gen_time):
    """
    Generates end-to-end path at specified time
    :return: HTML formatted string for visualization
    """
    path_file=os.path.join(experience_full_path, f"paths/paths_{int(gen_time-gen_time%pas_maj_routage)*1000000}.txt")
    if not os.path.isfile(path_file):
        print("erreur fichier, vérifier temps de génération")
        exit(0)
        
    
    viz_string = ""
    with open(path_file, 'r') as f:
        lignes=f.readlines()
    for l in lignes:
        if l.startswith(src_dst_str):
            paire, temps, chemin=eval(l)
            break
    else:
        raise Exception("commodité non trouvée")

    shifted_epoch = (pd.to_datetime(EPOCH) + pd.to_timedelta(gen_time, unit='ms')).strftime(format='%Y/%m/%d %H:%M:%S.%f')
    print(shifted_epoch)

    def position_sat(sat):
        return str(math.degrees(sat["sat_obj"].sublong)) + "," \
                    + str(math.degrees(sat["sat_obj"].sublat)) + "," \
                    + str(sat["alt_km"] * 1000)
    def position(x):
        if x<NUM_SATS:
            return position_sat(sat_objs[x])
        objSol=city_details[x]
        return str(objSol["long_deg"]) + "," + str(objSol["lat_deg"]) + "," + str(objSol["alt_km"] * 1000)
    
    for i in range(len(sat_objs)):
        sat_objs[i]["sat_obj"].compute(shifted_epoch)
        viz_string += "var redSphere = viewer.entities.add({name : '', position: Cesium.Cartesian3.fromDegrees(" \
                     + position_sat(sat_objs[i])+"), "\
                     + "ellipsoid : {radii : new Cesium.Cartesian3(20000.0, 20000.0, 20000.0), "\
                     + "material : Cesium.Color.BLACK.withAlpha(1),}});\n"

    orbit_links = util.find_orbit_links(sat_objs, NUM_ORBS, NUM_SATS_PER_ORB)
    for key in orbit_links:
        sat1 = orbit_links[key]["sat1"]
        sat2 = orbit_links[key]["sat2"]
        viz_string += "viewer.entities.add({name : '', polyline: { positions: Cesium.Cartesian3.fromDegreesArrayHeights([" \
                      + position_sat(sat_objs[sat1])+ "," \
                      + position_sat(sat_objs[sat2]) + "]), " \
                      + "width: 0.5, arcType: Cesium.ArcType.NONE, " \
                      + "material: new Cesium.PolylineOutlineMaterialProperty({ " \
                      + "color: Cesium.Color.GREY.withAlpha(0.3), outlineWidth: 0, outlineColor: Cesium.Color.BLACK})}});"

    precObjid=None
    dernier=len(chemin)-1
    for p, objid in enumerate(chemin):
        if p==0 or p==dernier:
            viz_string += "var redSphere = viewer.entities.add({name : '', position: Cesium.Cartesian3.fromDegrees(" \
                        + position(objid) + "), " \
                        + "ellipsoid : {radii : new Cesium.Cartesian3(50000.0, 50000.0, 50000.0), " \
                        + "material : Cesium.Color.GREEN.withAlpha(1),}});\n"
        if precObjid is not None:      
            viz_string += "viewer.entities.add({name : '', polyline: { positions: Cesium.Cartesian3.fromDegreesArrayHeights([" \
                        + position(precObjid) + "," \
                        + position(objid) + "]), " \
                        + "width: 3.0, arcType: Cesium.ArcType.NONE, " \
                        + "material: new Cesium.PolylineOutlineMaterialProperty({ " \
                        + "color: Cesium.Color.RED.withAlpha(1.0), outlineWidth: 0, outlineColor: Cesium.Color.BLACK})}});"
        precObjid=objid
    return viz_string




if __name__=='__main__':
    main()
