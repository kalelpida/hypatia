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

from .graph_tools import *
from satgen.isls import *
from satgen.ground_stations import *
from satgen.tles import *
import exputil
import yaml
import cartopy
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


GROUND_STATION_USED_COLOR = "#3b3b3b"
GROUND_STATION_UNUSED_COLOR = "black"
SATELLITE_USED_COLOR = "#a61111"
SATELLITE_UNUSED_COLOR = "red"
ISL_COLOR = "#eb6b38"


def print_graphical_routes_and_rtt_lazy(
        base_output_dir, satellite_network_dir,
        dynamic_state_update_interval_ms,
        simulation_end_time_s, src, dst, fstates
):
    # Local shell
    local_shell = exputil.LocalShell()

    # Default output dir assumes it is done manual
    pdf_dir = base_output_dir + "/pdf"
    data_dir = base_output_dir + "/data"
    local_shell.make_full_dir(pdf_dir)
    local_shell.make_full_dir(data_dir)

    # Variables (load in for each thread such that they don't interfere)
    ground_stations = read_ground_stations_extended(satellite_network_dir + "/ground_stations.txt")
    tles = read_tles(satellite_network_dir + "/tles.txt")
    satellites = tles["satellites"]
    epoch = tles["epoch"]

    # Derivatives
    simulation_end_time_ns = simulation_end_time_s * 1000 * 1000 * 1000
    dynamic_state_update_interval_ns = dynamic_state_update_interval_ms * 1000 * 1000

    # For each time moment
    fstate = {}
    current_path = []
    for i_t, t in enumerate(range(0, simulation_end_time_ns, dynamic_state_update_interval_ns)):
        fstate.update(fstates[i_t])
        
        # Only if there is a new path, print new path
        new_path = get_path(src, dst, fstate)
        if current_path != new_path:

            # This is the new path
            current_path = new_path

            # Now we make a pdf for it
            pdf_filename = pdf_dir + "/graphics_%d_to_%d_time_%dms.pdf" % (src, dst, int(t / 1000000))
            f = plt.figure()
            
            # Projection
            ax = plt.axes(projection=ccrs.PlateCarree())

            # Background
            ax.add_feature(cartopy.feature.OCEAN, zorder=0)
            ax.add_feature(cartopy.feature.LAND, zorder=0, edgecolor='black', linewidth=0.2)
            ax.add_feature(cartopy.feature.BORDERS, edgecolor='gray', linewidth=0.2)
            
            # Time moment
            time_moment_str = str(epoch + t * u.ns)

            # Other satellites
            for node_id in range(len(satellites)):
                shadow_ground_station = create_basic_ground_station_for_satellite_shadow(
                    satellites[node_id],
                    str(epoch),
                    time_moment_str
                )
                latitude_deg = float(shadow_ground_station["latitude_degrees"])
                longitude_deg = float(shadow_ground_station["longitude_degrees"])

                # Other satellite
                plt.plot(
                    longitude_deg,
                    latitude_deg,
                    color=SATELLITE_UNUSED_COLOR,
                    fillstyle='none',
                    markeredgewidth=0.1,
                    markersize=0.5,
                    marker='^',
                )
                plt.text(
                    longitude_deg + 0.5,
                    latitude_deg,
                    str(node_id),
                    color=SATELLITE_UNUSED_COLOR,
                    fontdict={"size": 1}
                )

            # # ISLs
            # for isl in list_isls:
            #     ephem_body = satellites[isl[0]]
            #     ephem_body.compute(time_moment_str)
            #     from_latitude_deg = math.degrees(ephem_body.sublat)
            #     from_longitude_deg = math.degrees(ephem_body.sublong)
            #
            #     ephem_body = satellites[isl[1]]
            #     ephem_body.compute(time_moment_str)
            #     to_latitude_deg = math.degrees(ephem_body.sublat)
            #     to_longitude_deg = math.degrees(ephem_body.sublong)
            #
            #     # Plot the line
            #     if ground_stations[src - len(satellites)]["longitude_degrees"] <= \
            #        from_longitude_deg \
            #        <= ground_stations[dst - len(satellites)]["longitude_degrees"] \
            #        and \
            #        ground_stations[src - len(satellites)]["latitude_degrees"] <= \
            #        from_latitude_deg \
            #        <= ground_stations[dst - len(satellites)]["latitude_degrees"] \
            #        and \
            #        ground_stations[src - len(satellites)]["longitude_degrees"] <= \
            #        to_longitude_deg \
            #        <= ground_stations[dst - len(satellites)]["longitude_degrees"] \
            #        and \
            #        ground_stations[src - len(satellites)]["latitude_degrees"] <= \
            #        to_latitude_deg \
            #        <= ground_stations[dst - len(satellites)]["latitude_degrees"]:
            #             plt.plot(
            #         [from_longitude_deg, to_longitude_deg],
            #         [from_latitude_deg, to_latitude_deg],
            #         color='#eb6b38', linewidth=0.1, marker='',
            #         transform=ccrs.Geodetic(),
            #     )

            # Other ground stations
            for gid in range(len(ground_stations)):
                latitude_deg = float(ground_stations[gid]["latitude_degrees"])
                longitude_deg = float(ground_stations[gid]["longitude_degrees"])

                # Other ground station
                plt.plot(
                    longitude_deg,
                    latitude_deg,
                    color=GROUND_STATION_UNUSED_COLOR,
                    fillstyle='none',
                    markeredgewidth=0.2,
                    markersize=1.0,
                    marker='o',
                )
            
            # Lines between
            if current_path is not None:
                for v in range(1, len(current_path)):
                    from_node_id = current_path[v - 1]
                    to_node_id = current_path[v]

                    # From coordinates
                    if from_node_id < len(satellites):
                        shadow_ground_station = create_basic_ground_station_for_satellite_shadow(
                            satellites[from_node_id],
                            str(epoch),
                            time_moment_str
                        )
                        from_latitude_deg = float(shadow_ground_station["latitude_degrees"])
                        from_longitude_deg = float(shadow_ground_station["longitude_degrees"])
                    else:
                        from_latitude_deg = float(
                            ground_stations[from_node_id - len(satellites)]["latitude_degrees"]
                        )
                        from_longitude_deg = float(
                            ground_stations[from_node_id - len(satellites)]["longitude_degrees"]
                        )

                    # To coordinates
                    if to_node_id < len(satellites):
                        shadow_ground_station = create_basic_ground_station_for_satellite_shadow(
                            satellites[to_node_id],
                            str(epoch),
                            time_moment_str
                        )
                        to_latitude_deg = float(shadow_ground_station["latitude_degrees"])
                        to_longitude_deg = float(shadow_ground_station["longitude_degrees"])
                    else:
                        to_latitude_deg = float(
                            ground_stations[to_node_id - len(satellites)]["latitude_degrees"]
                        )
                        to_longitude_deg = float(
                            ground_stations[to_node_id - len(satellites)]["longitude_degrees"]
                        )

                    # Plot the line
                    ax.plot(
                        [from_longitude_deg, to_longitude_deg],
                        [from_latitude_deg, to_latitude_deg],
                        color=ISL_COLOR, linewidth=0.5, marker='',
                        transform=ccrs.PlateCarree(),# or ccrs.Geodetic()
                    )

            # Across all points, we need to find the latitude / longitude to zoom into
            # min_latitude = min(
            #     ground_stations[src - len(satellites)]["latitude_degrees"],
            #     ground_stations[dst - len(satellites)]["latitude_degrees"]
            # )
            # max_latitude = max(
            #     ground_stations[src - len(satellites)]["latitude_degrees"],
            #     ground_stations[dst - len(satellites)]["latitude_degrees"]
            # )
            # min_longitude = min(
            #     ground_stations[src - len(satellites)]["longitude_degrees"],
            #     ground_stations[dst - len(satellites)]["longitude_degrees"]
            # )
            # max_longitude = max(
            #     ground_stations[src - len(satellites)]["longitude_degrees"],
            #     ground_stations[dst - len(satellites)]["longitude_degrees"]
            # )

            # Points
            if current_path is not None:
                for v in range(0, len(current_path)):
                    node_id = current_path[v]
                    if node_id < len(satellites):
                        shadow_ground_station = create_basic_ground_station_for_satellite_shadow(
                            satellites[node_id],
                            str(epoch),
                            time_moment_str
                        )
                        latitude_deg = float(shadow_ground_station["latitude_degrees"])
                        longitude_deg = float(shadow_ground_station["longitude_degrees"])
                        # min_latitude = min(min_latitude, latitude_deg)
                        # max_latitude = max(max_latitude, latitude_deg)
                        # min_longitude = min(min_longitude, longitude_deg)
                        # max_longitude = max(max_longitude, longitude_deg)
                        # Satellite
                        plt.plot(
                            longitude_deg,
                            latitude_deg,
                            color=SATELLITE_USED_COLOR,
                            marker='^',
                            markersize=0.65,
                        )
                        plt.text(
                            longitude_deg + 0.9,
                            latitude_deg,
                            str(node_id),
                            fontdict={"size": 2, "weight": "bold"}
                        )
                    else:
                        latitude_deg = float(ground_stations[node_id - len(satellites)]["latitude_degrees"])
                        longitude_deg = float(ground_stations[node_id - len(satellites)]["longitude_degrees"])
                        # min_latitude = min(min_latitude, latitude_deg)
                        # max_latitude = max(max_latitude, latitude_deg)
                        # min_longitude = min(min_longitude, longitude_deg)
                        # max_longitude = max(max_longitude, longitude_deg)
                        if v == 0 or v == len(current_path) - 1:
                            # Endpoint (start or finish) ground station
                            plt.plot(
                                longitude_deg,
                                latitude_deg,
                                color=GROUND_STATION_USED_COLOR,
                                marker='o',
                                markersize=0.9,
                            )
                        else:
                            # Intermediary ground station
                            plt.plot(
                                longitude_deg,
                                latitude_deg,
                                color=GROUND_STATION_USED_COLOR,
                                marker='o',
                                markersize=0.9,
                            )

            # Zoom into region
            # ax.set_extent([
            #     min_longitude - 5,
            #     max_longitude + 5,
            #     min_latitude - 5,
            #     max_latitude + 5,
            # ])

            # Legend
            ax.legend(
                handles=(
                    Line2D([0], [0], marker='o', label="Ground station (used)",
                            linewidth=0, color='#3b3b3b', markersize=5),
                    Line2D([0], [0], marker='o', label="Ground station (unused)",
                            linewidth=0, color='black', markersize=5, fillstyle='none', markeredgewidth=0.5),
                    Line2D([0], [0], marker='^', label="Satellite (used)",
                            linewidth=0, color='#a61111', markersize=5),
                    Line2D([0], [0], marker='^', label="Satellite (unused)",
                            linewidth=0, color='red', markersize=5, fillstyle='none', markeredgewidth=0.5),
                ),
                loc='lower left',
                fontsize='xx-small'
            )
            # Save final PDF figure
            f.savefig(pdf_filename, bbox_inches='tight')
            plt.close(f)
    print(f"plot path {src}->{dst} finished")
