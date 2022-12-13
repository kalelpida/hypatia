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
sys.path.append("../../satgenpy")
import satgen
import math
import yaml

# WGS72 value; taken from https://geographiclib.sourceforge.io/html/NET/NETGeographicLib_8h_source.html
EARTH_RADIUS= 6378135.0
MU_EARTH= 3.98574405e+14
SECONDS_SIDEREAL_DAY= 86164


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
        
        ALTITUDE_M = cstl_dico['ALTITUDE_M']
        SATELLITE_CONE_RADIUS_M = self.ALTITUDE_M / math.tan(math.radians(35.0))  # Considering an elevation angle of 35 degrees;
        MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(self.ALTITUDE_M, 2))
        # ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
        MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + self.ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))

        self.BASE_NAME = cstl_dico['BASE_NAME']
        self.NICE_NAME = cstl_dico['NICE_NAME']
        self.ECCENTRICITY = cstl_dico['ECCENTRICITY']
        self.ARG_OF_PERIGEE_DEGREE = cstl_dico['ARG_OF_PERIGEE_DEGREE']
        self.PHASE_DIFF = cstl_dico['PHASE_DIFF']
        self.MEAN_MOTION_REV_PER_DAY = SECONDS_SIDEREAL_DAY*math.sqrt(MU_EARTH/(self.ALTITUDE_M+EARTH_RADIUS)**3)/math.pi/2  # ~14.5 revs/jour
        
        self.MAX_GSL_LENGTH_M = MAX_GSL_LENGTH_M
        self.MAX_ISL_LENGTH_M = MAX_ISL_LENGTH_M
        self.NUM_ORBS = cstl_dico['NUM_ORBS']
        self.NUM_SATS_PER_ORB = cstl_dico['NUM_SATS_PER_ORB']
        self.INCLINATION_DEGREE = cstl_dico['INCLINATION_DEGREE']

    def init_ground_stations(self):
        # Add base name to setting
        name = self.BASE_NAME + "_" + self.config['isls'] + "_" + self.config['sol'] + "_" + self.config['algo']

        # Create output directories
        if not os.path.isdir(self.output_generated_data_dir):
            os.makedirs(self.output_generated_data_dir, exist_ok=True)
        if not os.path.isdir(self.output_generated_data_dir + "/" + name):
            os.makedirs(self.output_generated_data_dir + "/" + name, exist_ok=True)

        # Ground stations
        print("Generating ground stations...")
        if self.config['sol'] == "ground_stations_top_100":
            satgen.extend_ground_stations(
                "input_data/ground_stations_cities_sorted_by_estimated_2025_pop_top_100.basic.txt",
                self.output_generated_data_dir + "/" + name + "/ground_stations.txt"
            )
        elif self.config['sol'] == "ground_stations_paris_moscow_grid":
            satgen.extend_ground_stations(
                "input_data/ground_stations_paris_moscow_grid.basic.txt",
                self.output_generated_data_dir + "/" + name + "/ground_stations.txt"
            )
        elif self.config['sol'].startswith("users_and_main_stations"):
            NbUsers=int(self.config['sol'].removeprefix("users_and_main_stations"))
            satgen.extend_stations_and_users(
                "input_data/ground_stations_cities_sorted_by_estimated_2025_pop_top_100.basic.txt",
                filename_users_in, NbUsers, AFAIRE
                self.output_generated_data_dir + "/" + name + "/ground_stations.txt"
            )
        else:
            raise ValueError("Unknown ground station selection: " + self.config['sol'])

    def calculate(self,      
    ):

        # Add base name to setting
        name = self.BASE_NAME + "_" + self.config['isls'] + "_" + self.config['sol'] + "_" + self.config['algo']


        # TLEs
        print("Generating TLEs...")
        satgen.generate_tles_from_scratch_manual(
            self.output_generated_data_dir + "/" + name + "/tles.txt",
            self.NICE_NAME,
            self.NUM_ORBS,
            self.NUM_SATS_PER_ORB,
            self.PHASE_DIFF,
            self.INCLINATION_DEGREE,
            self.ECCENTRICITY,
            self.ARG_OF_PERIGEE_DEGREE,
            self.MEAN_MOTION_REV_PER_DAY
        )

        # ISLs
        print("Generating ISLs...")
        if self.config['isls'] == "isls_plus_grid":
            satgen.generate_plus_grid_isls(
                self.output_generated_data_dir + "/" + name + "/isls.txt",
                self.NUM_ORBS,
                self.NUM_SATS_PER_ORB,
                isl_shift=0,
                idx_offset=0
            )
        elif self.config['isls'] == "isls_none":
            satgen.generate_empty_isls(
                self.output_generated_data_dir + "/" + name + "/isls.txt"
            )
        else:
            raise ValueError("Unknown ISL selection: " + self.config['isls'])

        # Description
        print("Generating description...")
        satgen.generate_description(
            self.output_generated_data_dir + "/" + name + "/description.txt",
            self.MAX_GSL_LENGTH_M,
            self.MAX_ISL_LENGTH_M
        )

        # GSL interfaces
        ground_stations = satgen.read_ground_stations_extended(
            self.output_generated_data_dir + "/" + name + "/ground_stations.txt"
        )
        if self.config['algo'] == "algorithm_free_one_only_gs_relays" \
                or self.config['algo'] == "algorithm_free_one_only_over_isls"\
				or self.config['algo'] == "algorithm_free_one_only_over_isls2"\
                or self.config['algo'] == "algorithm_free_one_only_over_isls2b"\
                or self.config['algo'] == "algorithm_free_one_only_over_isls2c"\
                or self.config['algo'] == "algorithm_free_one_only_over_isls2d"\
                or self.config['algo'] == "algorithm_free_one_only_over_isls2e"\
                or self.config['algo'] == "algorithm_free_one_only_over_isls3"\
                or self.config['algo'] == "algorithm_free_one_only_over_isls4":
            gsl_interfaces_per_satellite = 1
        elif self.config['algo'] == "algorithm_paired_many_only_over_isls":
            gsl_interfaces_per_satellite = len(ground_stations)
        else:
            raise ValueError("Unknown dynamic state algorithm: " + self.config['algo'])

        print("Generating GSL interfaces info..")
        satgen.generate_simple_gsl_interfaces_info(
            self.output_generated_data_dir + "/" + name + "/gsl_interfaces_info.txt",
            self.NUM_ORBS * self.NUM_SATS_PER_ORB,
            len(ground_stations),
            gsl_interfaces_per_satellite,  # GSL interfaces per satellite
            1,  # (GSL) Interfaces per ground station
            1,  # Aggregate max. bandwidth satellite (unit unspecified)
            1   # Aggregate max. bandwidth ground station (same unspecified unit)
        )

        # Forwarding state
        print("Generating forwarding state...")
        satgen.help_dynamic_state(
            self.output_generated_data_dir,
            self.config['threads'],  # Number of threads
            name,
            self.config['pas'],
            self.config['duree'],
            self.MAX_GSL_LENGTH_M,
            self.MAX_ISL_LENGTH_M,
            self.config['algo'],
            True
        )
