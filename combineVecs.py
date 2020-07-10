#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Combine vector representations generated by RNN/GRU/LSTM networks
"""

# Add parent path so we can import modules
import sys
sys.path.insert(0,'..')

from argparse import ArgumentParser
import glob
import numpy as np
import os
import pandas as pd
import shutil
import sys
import time

import torch

start_time = time.time()

from utils import read_input_file
from utils import sort_key
from utils import read_command_combinevecs
# --- set seed for reproducibility
from utils import set_seed_everywhere
set_seed_everywhere(1364)

# ------------------- combine_vecs --------------------
def combine_vecs(input_file_path="default", qc_modes=["q", "c"], rnn_passes=["fwd", "bwd"],
                 input_scenario="test", output_scenario="test", print_every=500):
    
    if type(rnn_passes) in [str]:
        rnn_passes = rnn_passes.split(",")
    rnn_passes = [x.strip() for x in rnn_passes]
    
    if type(qc_modes) in [str]:
        qc_modes = qc_modes.split(",")
    qc_modes = [x.strip() for x in qc_modes]
    
    for qc_mode in qc_modes:
        for rnn_pass in rnn_passes:
            # paths to create tensors/arrays
            outputpath = os.path.join("combined", output_scenario)
            if not os.path.isdir(outputpath):
                os.makedirs(outputpath)
    
            if qc_mode == "q":
                query_candidate_mode = "queries"
            elif qc_mode == "c":
                query_candidate_mode = "candidates"
        
            # Set path according to query/candidate mode
            path2vecs = os.path.join(query_candidate_mode, input_scenario, 
                                     f"embed_{query_candidate_mode}", 
                                     "rnn_" + rnn_pass + "*")
            path2ids = os.path.join(query_candidate_mode, input_scenario, 
                                    f"embed_{query_candidate_mode}", "rnn_indxs*")
            pathdf = os.path.join(query_candidate_mode, input_scenario, f"{query_candidate_mode}.df")
            path_vec_combined = os.path.join(outputpath, f"{query_candidate_mode}_{rnn_pass}.pt")
            path_id_combined = os.path.join(outputpath, f"{query_candidate_mode}_{rnn_pass}_id.pt")
            path_items_combined = os.path.join(outputpath, f"{query_candidate_mode}_{rnn_pass}_items.npy")
            inp_par_dir = os.path.join(query_candidate_mode, input_scenario)
            
            if input_file_path in ["default"]:
                detect_input_files = glob.iglob(os.path.join(inp_par_dir, "*.yaml"))
                for detected_inp in detect_input_files:
                    if os.path.isfile(detected_inp):
                        shutil.copy2(detected_inp, outputpath)
                        input_file_path = detected_inp
            else:
                shutil.copy2(input_file_path, outputpath)
            
            dl_inputs = read_input_file(input_file_path)
            
            print("\n\n-- Combine vectors")
            print(f"Reading vectors from {path2vecs}")
            list_files = glob.glob(os.path.join(path2vecs))
            list_files.sort(key=sort_key)
            vecs = []
            for i, lfile in enumerate(list_files):
                if i % print_every == 0: print("%07i" % i, lfile)
                if len(vecs) == 0:
                    vecs = torch.load(f"{lfile}", map_location=dl_inputs['general']['device'])
                else:
                    vecs = torch.cat((vecs, torch.load(f"{lfile}", map_location=dl_inputs['general']['device'])))
            print()
            # Save combined vectors
            torch.save(vecs, path_vec_combined)
            
            print("\n-- Combine IDs")
            list_files = glob.glob(os.path.join(path2ids))
            list_files.sort(key=sort_key)
            vecs_ids = []
            for i, lfile in enumerate(list_files): 
                if i % print_every == 0: print("%07i" % i, lfile)
                if len(vecs_ids) == 0:
                    vecs_ids = torch.load(f"{lfile}", map_location=dl_inputs['general']['device'])
                else:
                    vecs_ids = torch.cat((vecs_ids, torch.load(f"{lfile}", dl_inputs['general']['device'])))
            print()
            # Save combined IDs
            torch.save(vecs_ids, path_id_combined)
            
            # Save strings for the first column in queries/candidates files
            mydf = pd.read_pickle(pathdf)
            vecs_items = mydf['s1_unicode'].to_numpy()
            np.save(path_items_combined, vecs_items)
    
    print("--- %s seconds ---" % (time.time() - start_time))

def main():
    # --- read args from the command line
    qc_modes, input_scenario, rnn_passes, output_scenario, input_file_path = \
        read_command_combinevecs()

    # --- 
    combine_vecs(input_file_path=input_file_path, 
                 qc_modes=qc_modes, 
                 rnn_passes=rnn_passes,
                 input_scenario=input_scenario, 
                 output_scenario=output_scenario)

if __name__ == '__main__':
    main()
