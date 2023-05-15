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
import sys, yaml
local_shell = exputil.LocalShell()

# Clear old runs
#local_shell.perfect_exec("rm -rf runs/*/logs_ns3")

# Get workload identifier from argument
num_machines = 1
args = sys.argv[1:]
if int(args[0]) < 0 or int(args[0]) >= num_machines:
    raise ValueError("Need to have have first argument in range [0, %d) to pick workload" % num_machines)
workload_id = int(args[0])
config_file = args[1]
with open(config_file, 'r') as f:
	    dico_params=yaml.load(f, Loader=yaml.Loader)

graine=dico_params.pop('graine')
duration_s=dico_params.get('duree')
algo = dico_params.get('algo')

# One-by-one run all experiments (such that they don't interfere with each other)
unique_id = 0


all_protocols_name = {dic['nom'] for dic in dico_params['protocoles'].values()} #["tcp", "udp"]:
protocol_chosen_name= '_and_'.join(sorted(list(all_protocols_name)))

if (unique_id % num_machines) == workload_id:

	# Prepare run directory
	run_dir = "runs/run_loaded_tm_pairing_for_%ds_with_%s_%s" % (
		duration_s, protocol_chosen_name, algo
	)
	logs_ns3_dir = run_dir + "/logs_ns3"
	local_shell.remove_force_recursive(logs_ns3_dir)
	local_shell.make_full_dir(logs_ns3_dir)

	# Perform run
	local_shell.perfect_exec(
		"cd ../../ns3-sat-sim/simulator; "
		#"NS_LOG='GSLNetDevice=level_logic:PointToPointLaserNetDevice=level_logic:PointToPointTracenNetDevice=level_logic' "
		"./waf --run=\"main_satnet "
		"--run_dir='../../papier2/ns3_experiments/" + run_dir + "'\""
		" 2>&1 | tee '../../papier2/ns3_experiments/" + logs_ns3_dir + "/console.txt'",
		output_redirect=exputil.OutputRedirect.CONSOLE
	)

	unique_id += 1
