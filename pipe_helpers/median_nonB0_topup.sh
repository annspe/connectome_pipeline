#!/usr/bin/env bash


data_dir=$1
dwiextract $data_dir/processing/dti/biascorr.mif - -no_bzero | mrmath - median $data_dir/processing/dti/median_nonbzero.mif -axis 3
echo "Median of non-b0 image was created"