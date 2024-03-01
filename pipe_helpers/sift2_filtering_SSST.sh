#!/usr/bin/env bash

# This script filters accroding to the SIFT2 algorithm provided by MRtrix3 the tractograms.
# It takes three user inputs: 
# 1) path (=base_dir + subj)
# 2) number of tracts to how many the total connectome should be reduced 
# 3) original number of tracts (which is based on the script running beforehand, creating the tractogram) 


### A) TAKING USER INPUT:

data_directory=$1 # first user input. This must be base_dir + subj
new_num_tr=$2 # number of tracts to which the tractograms should get reduced to after filtering
((new_num_mio=$new_num_tr/1000000)) # arithmetic operation to get the number of millions
orig_num_tr=$3 # number of tracts of the input tractogram
((orig_num_mio=$orig_num_tr/1000000)) # arithmetic operation to get the number of millions



### B) FILTERING: 
# Filtering with SIFT2 for the single_tissue data
cd $data_directory/processing/tractography/single_tissue
tcksift2 -force -act 5tt_regtodwi.mif tracks_$((orig_num_mio))mio.tck wm_tournier_fod.mif tck2_weights.txt -out_mu SIFT2_mu.txt -out_coeffs tck2_coeffs.txt -csv sift2_stats.csv 



