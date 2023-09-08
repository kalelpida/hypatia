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

# Contains few utility functions

import ephem
import math


def read_city_details(city_details_list, city_detail_file, offset=0):
    """
    Reads city-wise details
    :param city_details_list: List to be populated
    :param city_detail_file: Input file
    :return: city_details_list
    """
    lines = [line.rstrip('\n') for line in open(city_detail_file)]
    for i in range(len(lines)):
        val = lines[i].split(",")
        city_details_list[int(val[0])+offset] = {
            "name": val[1],
            "lat_deg": val[2],
            "long_deg": val[3],
            "alt_km": 0
        }
    return city_details_list

def read_ground_objects_file(city_detail_file, offset=0):
    """
    Reads city-wise details
    :param city_details_list: List to be populated
    :param city_detail_file: Input file
    :return: city_details_list
    """
    city_details={}
    with open(city_detail_file) as f:
        lines=f.readlines()
    for l in lines:
        val = l.rstrip('\n').split(",")
        city_details[int(val[0])+offset] = {
            "name": val[1],
            "lat_deg": val[2],
            "long_deg": val[3],
            "alt_km": 0
        }
    return city_details


def generate_sat_obj_list(
        num_orbit,
        num_sats_per_orbit,
        epoch,
        phase_diff,
        inclination,
        eccentricity,
        arg_perigee,
        mean_motion,
        altitude
):
    """
    Generates list of satellite objects based on orbital elements
    :param num_orbit: Number of orbits
    :param num_sats_per_orbit: Number of satellites per orbit
    :param epoch: Epoch (start time)
    :param phase_diff: Phase difference between adjacent orbits
    :param inclination: Angle of inclination
    :param eccentricity: Eccentricity of orbits
    :param arg_perigee: Argument of perigee of orbits
    :param mean_motion: Mean motion in revolutions per day
    :param altitude: Altitude in metres
    :return: List of satellite objects
    """
    sat_objs = [None] * (num_orbit * num_sats_per_orbit)
    counter = 0
    for orb in range(0, num_orbit):
        raan = orb * 360 / num_orbit
        orbit_wise_shift = 0
        if orb % 2 == 1:
            if phase_diff:
                orbit_wise_shift = 360 / (num_sats_per_orbit * 2)

        for n_sat in range(0, num_sats_per_orbit):
            mean_anomaly = orbit_wise_shift + (n_sat * 360 / num_sats_per_orbit)

            sat = ephem.EarthSatellite()
            sat._epoch = epoch
            sat._inc = ephem.degrees(inclination)
            sat._e = eccentricity
            sat._raan = ephem.degrees(raan)
            sat._ap = arg_perigee
            sat._M = ephem.degrees(mean_anomaly)
            sat._n = mean_motion

            sat_objs[counter] = {
                "sat_obj": sat,
                "alt_km": altitude / 1000,
                "orb_id": orb,
                "orb_sat_id": n_sat

            }
            counter += 1
    return sat_objs


def get_neighbor_satellite(
        sat1_orb,
        sat1_rel_id,
        sat2_orb,
        sat2_rel_id,
        sat_positions,
        num_orbits,
        num_sats_per_orbit):
    """
    Get satellite id of neighboring satellite
    :param sat1_orb: Orbit id of satellite
    :param sat1_rel_id: Relative index of satellite within orbit
    :param sat2_orb: Relative orbit of neighbor
    :param sat2_rel_id: Relative index of neighbor
    :param sat_positions: List of satellite objects
    :param num_orbits: Number of orbits
    :param num_sats_per_orbit: Number of satellites per orbit
    :return: satellite id of neighboring satellite
    """
    neighbor_abs_orb = (sat1_orb + sat2_orb) % num_orbits
    neighbor_abs_pos = (sat1_rel_id + sat2_rel_id) % num_sats_per_orbit
    sel_sat_id = -1
    for i in range(0, len(sat_positions)):
        if sat_positions[i]["orb_id"] == neighbor_abs_orb and sat_positions[i]["orb_sat_id"] == neighbor_abs_pos:
            sel_sat_id = i
            break
    return sel_sat_id


def find_orbit_links(sat_positions, num_orbit, num_sats_per_orbit):
    """
    Orbit is visualized by connecting consecutive satellites within te orbit.
    This function returns such satellite-satellite connections
    :param sat_positions: List of satellite objects
    :param num_orbit: Number of orbits
    :param num_sats_per_orbit: Number of satellites per orbit
    :return: Components of orbit
    """
    orbit_links = {}
    cntr = 0
    for i in range(0, len(sat_positions)):
        sel_sat_id = get_neighbor_satellite(sat_positions[i]["orb_id"], sat_positions[i]["orb_sat_id"],
                                                 0, 1, sat_positions, num_orbit, num_sats_per_orbit)
        orbit_links[cntr] = {
            "sat1": i,
            "sat2": sel_sat_id,
            "dist": -1.0
        }
        cntr += 1
    return orbit_links


def find_grid_links(sat_positions, num_orbit, num_sats_per_orbit):
    """
    Generates +Grid connectivity between satellites
    :param sat_positions: List of satellite objects
    :param num_orbit: Number of orbits
    :param num_sats_per_orbit: Number of satellites per orbit
    :return: +Grid links
    """
    grid_links = {}
    cntr = 0
    for i in range(0, len(sat_positions)):
        sel_sat_id = get_neighbor_satellite(sat_positions[i]["orb_id"], sat_positions[i]["orb_sat_id"],
                                                 0, 1, sat_positions,
                                                 num_orbit, num_sats_per_orbit)
        grid_links[cntr] = {
            "sat1": i,
            "sat2": sel_sat_id,
            "dist": -1.0
        }
        cntr += 1
        sel_sat_id = get_neighbor_satellite(sat_positions[i]["orb_id"], sat_positions[i]["orb_sat_id"],
                                                 1, 0, sat_positions,
                                                 num_orbit, num_sats_per_orbit)
        grid_links[cntr] = {
            "sat1": i,
            "sat2": sel_sat_id,
            "dist": -1.0
        }
        cntr += 1
    #print("num links:", cntr)
    return grid_links


def generate_sat_obj_position_list(
        num_orbit,
        num_sats_per_orbit,
        epoch,
        phase_diff,
        inclination,
        eccentricity,
        arg_perigee,
        mean_motion,
        altitude,
        current_time,
):
    """
    Generates list of satellite objects based on orbital elements
    :param num_orbit: Number of orbits
    :param num_sats_per_orbit: Number of satellites per orbit
    :param epoch: Epoch (start time)
    :param phase_diff: Phase difference between adjacent orbits
    :param inclination: Angle of inclination
    :param eccentricity: Eccentricity of orbits
    :param arg_perigee: Argument of perigee of orbits
    :param mean_motion: Mean motion in revolutions per day
    :param altitude: Altitude in metres
    :return: List of satellite objects
    """
    sat_objs = [None] * (num_orbit * num_sats_per_orbit)
    counter = 0
    for orb in range(0, num_orbit):
        raan = orb * 360 / num_orbit
        orbit_wise_shift = 0
        if orb % 2 == 1:
            if phase_diff:
                orbit_wise_shift = 360 / (num_sats_per_orbit * 2)

        for n_sat in range(0, num_sats_per_orbit):
            mean_anomaly = orbit_wise_shift + (n_sat * 360 / num_sats_per_orbit)

            sat = ephem.EarthSatellite()
            sat._epoch = epoch
            sat._inc = ephem.degrees(inclination)
            sat._e = eccentricity
            sat._raan = ephem.degrees(raan)
            sat._ap = arg_perigee
            sat._M = ephem.degrees(mean_anomaly)
            sat._n = mean_motion

            sat.compute(current_time)

            sat_objs[counter] = {
                "alt_m": altitude,
                "orb_id": orb,
                "orb_sat_id": n_sat,
                "lon": math.degrees(sat.sublong),
                "lat":math.degrees(sat.sublat),
                "type": "sat",
            }
            counter += 1
    return sat_objs

def generate_sol_obj_position_list(nom_fic):
    liste=[]
    with open(nom_fic, 'r') as f:
        for line in f:
            #0,Tokyo,35.689500,139.691710,0.000000,-3954843.592378,3354935.154958,3700263.820217,gateway
            idSolObj, ville, lat, lon, alt_m, _, _, _, objtype = line.strip().split(',') 
            liste.append({
                "alt_m": alt_m,
                "gs_id": int(idSolObj),
                "lat": lat,
                "lon": lon,
                "type": objtype
            })
    assert int(idSolObj) == len(liste)-1
    return liste

def utilcolor(utilization):
    blue_weight=0
    seuil_haut=0.9
    seuil_bas=seuil_haut/2
    if utilization < seuil_bas:
        green_weight = 255
        red_weight = 255 - round(255 * (seuil_bas - utilization) / seuil_bas)
    elif utilization < seuil_haut:
        red_weight = 255
        green_weight = 0 + round(255 * (seuil_haut - utilization) / seuil_bas)
    else:
        green_weight=0
        coeff=(utilization - seuil_haut)/(1 -seuil_haut)
        bleu=2 #between 0 (max red) and 4 (max blue), reached at mean([seuil_haut, 1])
        clarte=0.7 # between 0 (violet, full blue+red) and +inf (black)
        red_weight = round(255 * (1 - coeff)**clarte)
        blue_weight = round(255 * (bleu*coeff*(1 - coeff))**clarte)
    return '%02x%02x%02x' % (red_weight, green_weight, blue_weight) #hex_col 

def write_viz_files(viz_string, top_file, bottom_file, out_file):
    """
    Generates HTML visualization file
    :param viz_string: HTML formatted string
    :param top_file: top part of the HTML file
    :param bottom_file: bottom part of the HTML file
    :param out_file: output HTML file
    :return: None
    """
    writer_html = open(out_file, 'w')
    with open(top_file, 'r') as fi:
        writer_html.write(fi.read())
    writer_html.write(viz_string)
    with open(bottom_file, 'r') as fb:
        writer_html.write(fb.read())
    writer_html.close()

if __name__ =='__main__':
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    import numpy as np
    nb=300
    x0=np.linspace(0, 1, nb, endpoint=False)
    x1=1/nb+x0
    fig, axs = plt.subplots(figsize=(5, 1))
    cols=['#'+utilcolor(u) for u in (x0+x1)/2]
    lc= LineCollection( [[[v1,0], [100*v2, 0]] for v1, v2 in zip(x0, x1)],  colors=cols, lw=500)
    axs.add_collection(lc)
    axs.set_ylim(-0.01, 0.01)
    axs.axes.get_yaxis().set_visible(False)
    axs.set_xlabel("utilisation (%)")
    fig.tight_layout()
    plt.savefig("colorscale.png")
    plt.show()
