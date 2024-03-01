#!/usr/bin/env bash

# This script uses freesurfer to segment the child's and/or adolescent brain and creates the 5tt for ACT 
# This script needs to be tested

base_dir=$1 
subject=$2
type=$3

# Create freesurfer directories 
mkdir -m777 $SUBJECTS_DIR/$subject
mkdir -m777 $SUBJECTS_DIR/$subject/mri
mkdir -m777 $SUBJECTS_DIR/$subject/mri/orig

# Convert nii.gz to mgz and save it to /orig folder
mri_convert $base_dir/$subject/t2/T2_SVRTK.nii.gz $SUBJECT_DIR/$subject/mri/orig/001.mgz 

# Run Freesurfer Pipeline to achieve segmentation 
if [[ "$type" == "t2" ]]; then 
recon-all subject $subject -T2 $base_dir/$subject/t2/T2_SVRTK.nii.gz -all 

elif [[ "$type" == "t1" ]]; then 
recon-all -s $base_dir/$subject -all #-i $base_dir/$subject/t2/T2_SVRTK.nii.gz -all

fi

# create 5tt for MRtrix

5ttgen freesurfer $SUBJECT_DIR/$subject/mri/aseg.mgz $base_dir/$subject/t2/Labels/5tt.mif
