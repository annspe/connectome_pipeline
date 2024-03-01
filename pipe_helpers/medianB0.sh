#!/usr/bin/env bash


data_dir=$1
mrconvert -force $data_dir/dti/dti.nii.gz $data_dir/dti/dti.mif -fslgrad $data_dir/dti/bvecs $data_dir/dti/bvals
dwiextract $data_dir/processing/dti/biascorr.mif - -bzero | mrmath - median $data_dir/processing/dti/median_bzero.mif -axis 3
echo "Median b0 image was created"