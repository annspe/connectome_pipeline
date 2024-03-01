#!/usr/bin/env bash

# This script makes changes to the ENA33 Atlas. 


base_dir=$1
subj=$2

conDir=$base_dir/$subj/processing/connectome/ENA33_improved



# b) Prepare ENA33 Atlas for Structural connectivity

# Deletes corpus callosum and lateral ventricles from ENA33 atlas
c3d $conDir/parcels_ENA33_improved_coreg.nii.gz -replace 91 0 92 0 93 0 -o $conDir/parcels_corr2_ENA33.nii.gz
# change dGM Labels to new numbers
c3d $conDir/parcels_corr2_ENA33.nii.gz -replace 94 91 95 92 96 93 97 94 98 95 99 96 100 97 101 98 102 99 103 100 104 101 105 102 106 103 107 104 -o $conDir/parcels_corr_ENA33_improved.nii.gz

# Cleanup
rm $conDir/parcels_corr2_ENA33.nii.gz
mrconvert -force $conDir/parcels_corr_ENA33_improved.nii.gz $conDir/nodes.mif
echo "Nodes were created for " $subj
                                                                      
