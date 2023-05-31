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
    ground_stations_basic = []
    gid = 0
    with open(filename_ground_stations_basic, 'r') as fic:
        if filename_ground_stations_basic.endswith('txt'):
            lecteur=csv.DictReader(fic, fieldnames=['gid', 'name', 'latitude_degrees', 'longitude_degrees', 'elevation_m', 'population_k'])
        elif filename_ground_stations_basic.endswith('csv'):
            lecteur=csv.DictReader(fic)
        else:
            raise Exception("fichier non reconnu")
        
        for ligne in lecteur:
            if int(ligne['gid']) != gid:
                raise ValueError("Ground station id must increment each line")
            ligne["name"]=ligne['name'].replace(',', " ~")
            ground_stations_basic.append(dict(ligne))
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
                "latitude_degrees": split[2],
                "longitude_degrees": split[3],
                "elevation_m": float(split[4]),
                "cartesian_x": float(split[5]),
                "cartesian_y": float(split[6]),
                "cartesian_z": float(split[7]),
                "type": split[8].strip(),
            }
            ground_stations_extended.append(ground_station_basic)
            gid += 1
    return ground_stations_extended
