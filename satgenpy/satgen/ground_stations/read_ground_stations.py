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
import csv

def read_ground_stations_basic(filename_ground_stations_basic):
    """
    Reads ground stations from the input file.

    :param filename_ground_stations_basic: Filename of ground stations basic (typically /path/to/ground_stations.txt)

    :return: List of ground stations
    """
    with open(filename_ground_stations_basic, 'r') as f:
        if filename_ground_stations_basic.endswith('txt'):
            return read_basic_txt(f)
        elif filename_ground_stations_basic.endswith('csv'):
            return read_basic_csv(f)
        else:
            raise Exception("fichier non reconnu")

def read_basic_txt(fic):
    """
    Reads ground stations from the input file.

    :param filename_ground_stations_basic: Filename of ground stations basic (typically /path/to/ground_stations.txt)

    :return: List of ground stations
    """
    ground_stations_basic = []
    gid = 0
    for line in fic:
        split = line.split(',')
        if len(split) != 5:
            raise ValueError("Basic ground station file has 5 columns")
        if int(split[0]) != gid:
            raise ValueError("Ground station id must increment each line")
        ground_station_basic = {
            "gid": gid,
            "name": split[1],
            "latitude_degrees_str": split[2],
            "longitude_degrees_str": split[3],
            "elevation_m_float": float(split[4]),
        }
        ground_stations_basic.append(ground_station_basic)
        gid += 1
    return ground_stations_basic

def read_basic_csv(fic):
    """
    Reads ground stations from the input file.

    :param filename_ground_stations_basic: Filename of ground stations basic (typically /path/to/ground_stations.txt)

    :return: List of ground stations
    """
    lecteur=csv.reader(fic, dialect='excel')

    ground_stations_basic = []
    gid = 0
    for ligne in lecteur:
        if len(ligne) != 6:
            raise ValueError("Basic ground station file has 5 columns")
        if not ligne[0].isdecimal():
            continue
        if int(ligne[0]) != gid:
            raise ValueError("Ground station id must increment each line")
        ground_station_basic = {
            "gid": gid,
            "name": ligne[1],
            "latitude_degrees_str": ligne[2],
            "longitude_degrees_str": ligne[3],
            "elevation_m_float": float(ligne[4]),
            "population_k": int(ligne[5])
        }
        ground_stations_basic.append(ground_station_basic)
        gid += 1
    return ground_stations_basic

def read_ground_stations_extended(filename_ground_stations_extended):
    """
    Reads ground stations from the input file.

    :param filename_ground_stations_extended: Filename of ground stations basic (typically /path/to/ground_stations.txt)

    :return: List of ground stations
    """
    ground_stations_extended = []
    gid = 0
    with open(filename_ground_stations_extended, 'r') as f:
        for line in f:
            split = line.split(',')
            if len(split) != 9:
                raise ValueError("Extended ground station file has 9 columns: " + line)
            if int(split[0]) != gid:
                raise ValueError("Ground station id must increment each line")
            ground_station_basic = {
                "gid": gid,
                "name": split[1],
                "latitude_degrees_str": split[2],
                "longitude_degrees_str": split[3],
                "elevation_m_float": float(split[4]),
                "cartesian_x": float(split[5]),
                "cartesian_y": float(split[6]),
                "cartesian_z": float(split[7]),
                "type": split[8].strip(),
            }
            ground_stations_extended.append(ground_station_basic)
            gid += 1
    return ground_stations_extended
