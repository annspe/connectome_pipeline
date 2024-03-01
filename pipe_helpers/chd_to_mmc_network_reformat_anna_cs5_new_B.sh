#!/bin/bash


input_file=$1

echo $input_file

mrgrid -quiet -voxel 0.4,0.4,0.4 -interp cubic $input_file regrid ${input_file::-7}_resized.nii.gz

fslroi ${input_file::-7}_resized.nii.gz ${input_file::-7}_resized.nii.gz $(fslstats ${input_file::-7}_resized.nii.gz -w)

flirt -in ${input_file::-7}_resized.nii.gz -ref ${input_file::-18}/processing/t2/T2_SVRTK_reformatted.nii.gz -dof 12 -noresampblur -out ${input_file::-7}_flirt.nii.gz -cost mutualinfo -searchrx -180 180 -searchry -180 180 -searchrz -180 180

fslmaths ${input_file::-7}_flirt.nii.gz -thr 5 ${input_file::-7}_flirt.nii.gz

Slicer --launcher-no-splash --launch N4ITKBiasFieldCorrection --splinedistance 150 ${input_file::-7}_flirt.nii.gz ${input_file::-18}/processing/t2/T2_SVRTK_reformatted_trick.nii.gz


rm ${input_file::-7}_resized.nii.gz
rm ${input_file::-7}_flirt.nii.gz
