#!/usr/bin/env bash 
### CSD computation for ST and MT

# Input: rfe txt files


### A)TAKING USER INPUT:

data_directory=$1 # first user input. This must be base_dir + subj
tissue=$2 # SSST, SS3T, SS2T
pipe=$3


### B) Compute CSD depending on tissue & pipe  

if [ "$pipe" = "single_subject_alone" ]; then 
    if [ "$tissue" = "SSST" ]; then
    cd $data_directory/processing/tractography/single_tissue
    dwi2fod csd -mask ../../dti/mask.mif ../../dti/biascorr.mif response_wm_tournier.txt wm_tournier_fod.mif
    chmod a+rwx wm_tournier_fod.mif
    elif [ "$tissue" = "SS3T" ]; then
    cd $data_directory/processing/tractography/three_tissue
    ss3t_csd_beta1 ../../dti/biascorr.mif response_wm.txt wm_fod.mif response_gm.txt gm_fod.mif response_csf.txt csf_fod.mif -mask ../../dti/mask.mif #-fslgrad ../dti/bvecs ../dti/bvals
    chmod a+rwx ./wm_fod.mif
    chmod a+rwx ./gm_fod.mif
    chmod a+rwx ./csf_fod.mif
    elif [ "$tissue" = "SS2T" ]; then
    cd $data_directory/processing/tractography/two_tissue
    dwi2fod msmt_csd -mask ../../dti/mask.mif ../../dti/biascorr.nii.gz response_wm.txt wm_fod.mif response_csf.txt csf_fod.mif -fslgrad ../../dti/bvecs ../../dti/bvals
    chmod a+rwx ./wm_fod.mif
    chmod a+rwx ./csf_fod.mif
    fi
elif [ "$pipe" = "group_create_average" ]; then   # calculating FOD based on averaged RF 
    if [ "$tissue" = "SSST" ]; then 
    cd $PWD
    dwi2fod csd -mask $data_directory/processing/dti/mask.mif $data_directory/processing/dti/biascorr.mif ./GroupComparison/responsemean/response_sing_wm_mean.txt $data_directory/processing/tractography/single_tissue/wm_tournier_fod.mif
    cd $data_directory/processing/tractography/single_tissue
    chmod a+rwx wm_tournier_fod.mif
    elif [ "$tissue" = "SS3T" ]; then
    cd $PWD
    ss3t_csd_beta1 $data_directory/processing/dti/biascorr.mif ./GroupComparison/responsemean/response_threetiss_wm_mean.txt $data_directory/processing/tractography/three_tissue/wm_fod.mif ./GroupComparison/responsemean/response_threetiss_gm_mean.txt $data_directory/processing/tractography/three_tissue/gm_fod.mif ./GroupComparison/responsemean/response_threetiss_csf_mean.txt $data_directory/processing/tractography/three_tissue/csf_fod.mif 
    cd $data_directory/processing/tractography/three_tissue
    chmod a+rwx ./wm_fod.mif
    chmod a+rwx ./gm_fod.mif
    chmod a+rwx ./csf_fod.mif        
    elif [ "$tissue" = "SS2T" ]; then
    cd $PWD
    dwi2fod msmt_csd $data_directory/processing/dti/biascorr.mif ./GroupComparison/responsemean/response_twotiss_wm_mean.txt $data_directory/processing/tractography/two_tissue/wm_fod.mif ./GroupComparison/responsemean/response_twotiss_csf_mean.txt $data_directory/processing/tractography/two_tissue/csf_fod.mif 
    cd $data_directory/processing/tractography/two_tissue
    chmod a+rwx ./wm_fod.mif
    chmod a+rwx ./csf_fod.mif     
    fi
elif [ "$pipe" = "group_take_average" ]; then   # calculating FOD based on averaged RF 
    if [ "$tissue" = "SSST" ]; then 
    cd $PWD
    mkdir -m777 $data_directory/processing/tractography/single_tissue
    dwi2fod csd -mask $data_directory/processing/dti/mask.mif $data_directory/processing/dti/biascorr.mif ./GroupComparison/responsemean/response_sing_wm_mean.txt $data_directory/processing/tractography/single_tissue/wm_tournier_fod.mif
    cd $data_directory/processing/tractography/single_tissue
    chmod a+rwx wm_tournier_fod.mif
    elif [ "$tissue" = "SS3T" ]; then
    cd $PWD
    mkdir -m777 $data_directory/processing/tractography/three_tissue
    ss3t_csd_beta1 $data_directory/processing/dti/biascorr.mif ./GroupComparison/responsemean/response_threetiss_wm_mean.txt $data_directory/processing/tractography/three_tissue/wm_fod.mif ./GroupComparison/responsemean/response_threetiss_gm_mean.txt $data_directory/processing/tractography/three_tissue/gm_fod.mif ./GroupComparison/responsemean/response_threetiss_csf_mean.txt $data_directory/processing/tractography/three_tissue/csf_fod.mif 
    cd $data_directory/processing/tractography/three_tissue
    chmod a+rwx ./wm_fod.mif
    chmod a+rwx ./gm_fod.mif
    chmod a+rwx ./csf_fod.mif        
    elif [ "$tissue" = "SS2T" ]; then
    cd $PWD
    mkdir -m777 $data_directory/processing/tractography/two_tissue
    dwi2fod msmt_csd $data_directory/processing/dti/biascorr.mif ./GroupComparison/responsemean/response_twotiss_wm_mean.txt $data_directory/processing/tractography/two_tissue/wm_fod.mif ./GroupComparison/responsemean/response_twotiss_csf_mean.txt $data_directory/processing/tractography/two_tissue/csf_fod.mif 
    cd $data_directory/processing/tractography/two_tissue
    chmod a+rwx ./wm_fod.mif
    chmod a+rwx ./csf_fod.mif
    fi
fi


 






