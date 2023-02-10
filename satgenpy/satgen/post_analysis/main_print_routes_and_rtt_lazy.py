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

import sys
from satgen.post_analysis.print_routes_and_rtt_lazy import print_routes_and_rtt_lazy
from satgen.post_analysis.read_fstates import read_fstates
from multiprocessing import Pool
def main(args):
    if len(args) != 6:
        print("Must supply exactly six arguments")
        print("Usage: python -m satgen.post_analysis.main_print_graphical_routes_and_rtt.py [data_dir] "
              "[satellite_network_dir] [dynamic_state_update_interval_ms] [end_time_s] [num_threads] [commodities_file_path]")
        exit(1)
    
    with open(args[5], "r") as f:
        list_comms=eval(f.readline())
    

    core_network_folder_name = args[1].split("/")[-1]
    base_output_dir = "%s/%s/%dms_for_%ds/manual" % (
        args[0], core_network_folder_name, int(args[2]), int(args[3])
    )
    print("Data dir: " + args[0])
    print("Used data dir to form base output dir: " + base_output_dir)

    liste_args=[]
    fstates = read_fstates(args[1], int(args[2]), int(args[3]))
    for (src,dst,_) in list_comms:
        liste_args.append((base_output_dir, args[1], int(args[2]), int(args[3]), src, dst, "", fstates))# "": must be executed in satgenpy directory

    
    pool = Pool(int(args[4]))
    pool.starmap(print_routes_and_rtt_lazy, liste_args)
    pool.close()
    pool.join()


if __name__ == "__main__":
    main(sys.argv[1:])
