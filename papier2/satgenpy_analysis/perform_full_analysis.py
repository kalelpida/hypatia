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

import exputil
import sys
import os
import yaml
print("perform full anal")
local_shell = exputil.LocalShell()
max_num_processes = 6

# Check that no screen is running
if local_shell.count_screens() != 0:
    print("There is a screen already running. "
          "Please kill all screens before running this analysis script (killall screen).")
    exit(1)

# Re-create data directory
#local_shell.remove_force_recursive("data")
if not "data" in [obj for obj in os.listdir('.') if os.path.isdir(obj)]:
	local_shell.make_full_dir("data")
if not "command_logs" in [obj for obj in os.listdir('data') if os.path.isdir(obj)]:
	local_shell.make_full_dir("data/command_logs")

# Where to store all commands
commands_to_run = []

# Manual
config_fic = sys.argv[1]
with open(config_fic, 'r') as f:
    dico=yaml.load(f, Loader=yaml.Loader)
duree=dico['duree']
pas=dico['pas']
cstl=dico['constellation']
nom_fic='_'.join([cstl, dico['isls'], dico['sol'], dico['algo']])
print("Plot routes and RTT of commodities over time")

commodites_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../satellite_networks_state/commodites.temp")

os.chdir("../../satgenpy")
sys.path.append(os.getcwd())
import satgen

satgen.post_analysis.main_print_graphical_routes_and_rtt_lazy("../papier2/satgenpy_analysis/data ../papier2/satellite_networks_state/gen_data/"
                "{} "
                " {} {} {} {}".format(nom_fic,pas,duree,max_num_processes,commodites_path).split())

satgen.post_analysis.main_print_routes_and_rtt_lazy("../papier2/satgenpy_analysis/data ../papier2/satellite_networks_state/gen_data/"
                "{} "
                " {} {} {} {}".format(nom_fic,pas,duree,max_num_processes,commodites_path).split())


