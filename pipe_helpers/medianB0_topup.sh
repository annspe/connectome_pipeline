#!/usr/bin/env bash


data_dir=$1
dwiextract $data_dir/processing/dti/biascorr.mif - -bzero | mrmath - median $data_dir/processing/dti/median_bzero.mif -axis 3
echo "Median b0 image was created"