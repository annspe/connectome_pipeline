#!/usr/bin/env bash


data_dir=$1 # is the base_dir + subj
# Raw DTI data in nifti format gets transformed into mif format for mrtrix (change the paths if necessry)
mrconvert -force $data_dir/dti/dti.nii.gz $data_dir/dti/dti.mif -fslgrad $data_dir/dti/bvecs $data_dir/dti/bvals
# Extracts the bzero images and calculates the median of it (change the paths if neccessary)
dwiextract $data_dir/dti/dti.mif - -bzero | mrmath - median $data_dir/processing/dti/median_bzero.mif -axis 3
echo "Median b0 image was created"