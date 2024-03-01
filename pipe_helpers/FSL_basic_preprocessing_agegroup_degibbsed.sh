#!/usr/bin/env bash

######## Part 1 of basic FSL DTI preprocessing steps for neonatal cohort ###########

#### DEPENDENCIES: 
#### - cuda8.0
#### - fsl 

#### A) PREPARATIONS: DEFINING PATHS & DATA DIRECTORY 

# CUDA VERSION 8.0 IS NECCESSARY 


### A) 2. TAKING USER INPUT: 
data_directory=$1 # first user input. This must be base_dir + subj
age=$2 

cd $data_directory/


#### B) FOLLOW FSL PREPROCESSING STEPS 

#### 1) Create non-diffusion-weighted image from denoised dti data.
####### If the denoising should start from raw dti data, change the first input of fslroi

fslroi ./processing/dti/degibbs.nii.gz ./processing/dti/nodif 0 1 # takes first volume (=0) and Anzahl (=1) creates image called nodif


#### 2) TOPUP cant be run because there is only one single encoding direction
####    Therefore, eddy will be run now on the distored images

#### 3) Create a brain mask 
fslmaths ./processing/dti/nodif -Tmedian ./processing/dti/hifi_nodif # median is taken because of outliers
chmod a+rwx ./processing/dti/nodif.nii.gz
chmod a+rwx ./processing/dti/hifi_nodif.nii.gz

#### 4) Create binary brain mask
if [[ "$age" == "newborn" ]]; then 
bet ./processing/dti/hifi_nodif ./processing/dti/hifi_nodif_brain -m -f 0.2 # same parameters as fsl (Andras parameters did not work); 
# output will be hifi_nodif_brain_mask. check if the fit is good. 

elif [[ "$age" == "child" ]]; then
bet ./processing/dti/hifi_nodif ./processing/dti/hifi_nodif_brain -m -f 0.3 # parameter from Melanie's expertise
# output will be hifi_nodif_brain_mask. check if the fit is good. 

elif [[ "$age" == "adolescent" ]]; then
bet ./processing/dti/hifi_nodif ./processing/dti/hifi_nodif_brain -m -f 0.3 # parameter from Melanie's expertise 
# output will be hifi_nodif_brain_mask. check if the fit is good. 
fi

chmod a+rwx ./processing/dti/hifi_nodif_brain.nii.gz 
mrconvert ./processing/dti/hifi_nodif_brain_mask.nii.gz ./processing/dti/hifi_nodif_brain_mask.mif # convert it to the mrtrix format
chmod a+rwx ./processing/dti/hifi_nodif_brain_mask.mif 

#### 5) Create index and acqp text file needed for eddy
mkdir -m777 ./processing/dti/process
numframes=$(fslinfo ./dti/dti.nii.gz | grep dim4 | awk 'NR==1{print $2}') # dim4 describes number of volumes, in our case 36
indx=""
for ((i=1; i<=$numframes; i+=1)); do
	indx="$indx 1"
done
echo $indx > ./processing/dti/process/index.txt # index file
chmod a+rwx ./processing/dti/process/index.txt

if [[ "$age" == "newborn" ]]; then 
echo "0 -1 0 0.1" > ./processing/dti/process/acqp.txt # acqp file
elif [[ "$age" == "child" ]]; then
echo "0 -1 0 0.03" > ./processing/dti/process/acqp.txt # acqp file (otherwise try 0.1)
elif [[ "$age" == "adolescent" ]]; then
echo "0 -1 0 0.03" > ./processing/dti/process/acqp.txt # acqp file (otherwise try 0.1)
fi
chmod a+rwx ./processing/dti/process/acqp.txt

#### 6) Run eddy 
# if eddy_cuda8.0 does not work, only use eddy. However, simply eddy cant do slice-to-volume correction. Hence, the command --mporder needs to be deleted. 

# When running this script directly on CS5, this command like this works. 
if [[ "$age" == "newborn" ]]; then 
eddy_cuda8.0 --imain=./processing/dti/degibbs.nii.gz	--mask=./processing/dti/hifi_nodif_brain_mask.nii.gz --index=./processing/dti/process/index.txt	--acqp=./processing/dti/process/acqp.txt --bvecs=./dti/bvecs	--bvals=./dti/bvals --out=./processing/dti/eddy_images	--niter=6 --fwhm=10,6,4,2,0,0 --fep --repol --ol_nstd=4	--mporder=5 --s2v_niter=10 --verbose

elif [[ "$age" == "child" ]]; then
eddy_cuda8.0 --imain=./processing/dti/degibbs.nii.gz	--mask=./processing/dti/hifi_nodif_brain_mask.nii.gz --index=./processing/dti/process/index.txt	--acqp=./processing/dti/process/acqp.txt --bvecs=./dti/bvecs	--bvals=./dti/bvals --out=./processing/dti/eddy_images	--niter=5 --fwhm=10 --fep --repol --ol_nstd=4	--mporder=5 --s2v_niter=10 --verbose # almost default settings

elif [[ "$age" == "adolescent" ]]; then
eddy_cuda8.0 --imain=./processing/dti/degibbs.nii.gz	--mask=./processing/dti/hifi_nodif_brain_mask.nii.gz --index=./processing/dti/process/index.txt	--acqp=./processing/dti/process/acqp.txt --bvecs=./dti/bvecs	--bvals=./dti/bvals --out=./processing/dti/eddy_images	--niter=5 --fwhm=10 --fep --repol --ol_nstd=4	--mporder=5 --s2v_niter=10 --verbose # almost default settings 
fi

chmod a+rwx ./processing/dti/hifi_nodif_brain_mask.nii.gz 
chmod a+rwx ./processing/dti/eddy_images.nii.gz 
 

#  To check if eddy worked well, you can run Qualitiy Control FSL_QC_ofeddy_v1


