#!/usr/bin/env bash 
### Response function estimation with MRtrix

# Input: preprocessed dwi data (in my pipeline "eddy_images.nii.gz") 

### A)TAKING USER INPUT: 

data_directory=$1 # first user input. This must be base_dir + subj
tissue=$2 # SSST, SSS3T 
pipe=$3 # single_subject_alone, group_create_average 
subj=$4
script_dir=$5

## Create Mask: works for SSST, SS3T, SS2T
cd $data_directory/processing/dti
dwi2mask -force ./biascorr.mif ./mask.mif #-fslgrad ../dti/bvecs ../dti/bvals 
chmod a+rwx ./mask.mif

# SSST RF estimation. 
if [[ "$tissue" == "SSST" ]]; then
cd $data_directory/processing/tractography
mkdir -m777 single_tissue 
    if [[ "$pipe" == "single_subject_alone" ]]; then
    
    cd $data_directory/processing/tractography/single_tissue

    # Response function estimation: 
    dwi2response tournier ../../dti/bias_normcorr.mif response_wm_tournier.txt 
    chmod a+rwx ./response_wm_tournier.txt
    
    elif [[ "$pipe" == "group_create_average" ]]; then
    
    dwi2response tournier $script_dir/GroupComparison/dwinormalise/dwi_output/$subj.mif $data_directory/processing/tractography/single_tissue/response_wm_tournier.txt
    chmod a+rwx $data_directory/processing/tractography/single_tissue/response_wm_tournier.txt
    fi
fi

# SS3T RF estimation 
if [[ "$tissue" == "SS3T" ]]; then

cd $data_directory/processing/tractography
mkdir -m777 three_tissue
cd $data_directory/processing/tractography/three_tissue

# Response function estimation: 
dwi2response dhollander ../../dti/biascorr.mif response_wm.txt response_gm.txt response_csf.txt -voxels response_voxels.mif -fslgrad ../../../dti/bvecs ../../../dti/bvals
#
# Hint: open response_voxels.mif with mrview and overlay it with the dwi or t2 data. Like this you can check your response functions. 
chmod a+rwx ./response_wm.txt
chmod a+rwx ./response_gm.txt
chmod a+rwx ./response_csf.txt
chmod a+rwx ./response_voxels.mif

fi


# SS3T RF estimation 
if [[ "$tissue" == "SS2T" ]]; then

cd $data_directory/processing/tractography
mkdir -m777 two_tissue
cd $data_directory/processing/tractography/two_tissue

# Response function estimation: 
dwi2response dhollander ../../dti/biascorr.mif response_wm.txt response_gm.txt response_csf.txt -voxels response_voxels.mif -fslgrad ../../../dti/bvecs ../../../dti/bvals

# Hint: open response_voxels.mif with mrview and overlay it with the dwi or t2 data. Like this you can check your response functions. 

fi