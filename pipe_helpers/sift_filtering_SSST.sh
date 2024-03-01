#!/usr/bin/env bash

# This script filters accroding to the SIFT algorithm provided by MRtrix3 the tractograms.
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
# Filtering for the single_tissue data
cd $data_directory/processing/tractography/single_tissue
tcksift -force -act 5tt_regtodwi.mif -term_number $new_num_tr tracks_$((orig_num_mio))mio.tck wmtournier_fod_norm.mif sift_$((new_num_mio))mio.tck -out_mu SIFT_mu.txt
chmod a+rwx ./sift_$((new_num_mio))mio.tck


