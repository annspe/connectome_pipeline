#!/usr/bin/env bash

# Probabilistic whole brain tractography with ACT
# Based on single shell mutli tissue CSD 
# Receives two user inputs:
#  1) data directory = base_dir + subj
#  2) number of streamlines

### A)TAKING USER INPUT:

data_directory=$1 # first user input. This must be base_dir + subj
num_tracts=$2
seeding=$3
tissue=$4

if [ "$tissue" = "SS3T" ]; then
cd $data_directory/processing/tractography/three_tissue

### B) PREPARING FOR ACT

# 1) Intensity Normalisation: to correct for global intensitiy differences

mtnormalise -force wm_fod.mif wmfod_norm.mif gm_fod.mif gmfod_norm.mif csf_fod.mif csffod_norm.mif -mask ../../dti/mask.mif 
chmod a+rwx ./wmfod_norm.mif > /dev/null 2>&1
chmod a+rwx ./gmfod_norm.mif > /dev/null 2>&1
chmod a+rwx ./csffod_norm.mif > /dev/null 2>&1

# 2) Prepare mask of streamline seeding at grey/white matter boundary
#    Take the 5tt image which was coregistered to the diffusion space. 

## convert nii.gz to mif
mrconvert -force ../../t2/Labels/5tt_reg_to_dwi.nii.gz 5tt_regtodwi.mif 
chmod a+rwx ./5tt_regtodwi.mif > /dev/null 2>&1

    if [[ "$seeding" == "GMWM" ]]; then
    
    # create whitematter-greymatter boundery mask 
    5tt2gmwmi -force 5tt_regtodwi.mif gmwmSeed_reg.mif 
    chmod a+rwx ./gmwmSeed_reg.mif > /dev/null 2>&1
    
    # 3) Create streamlines
    #    Probabilistic tractography with 10 Mio streamlines
    
    tckgen -force -act 5tt_regtodwi.mif -backtrack -seed_gmwmi gmwmSeed_reg.mif -select $num_tracts wmfod_norm.mif tracks_$((num_tracts/1000000))mio.tck
    chmod a+rwx ./tracks_$((num_tracts/1000000))mio.tck > /dev/null 2>&1
    
    
    elif [[ "$seeding" == "dynamic" ]]; then
    
    tckgen -force -act 5tt_regtodwi.mif -backtrack -seed_dynamic wmfod_norm.mif -select $num_tracts wmfod_norm.mif tracks_$((num_tracts/1000000))mio.tck
    chmod a+rwx ./tracks_$((num_tracts/1000000))mio.tck > /dev/null 2>&1
    
    fi
elif [ "$tissue" = "SS2T" ]; then
cd $data_directory/processing/tractography/two_tissue
    
### B) PREPARING FOR ACT

# 1) Intensity Normalisation: to correct for global intensitiy differences

mtnormalise -force wm_fod.mif wmfod_norm.mif csf_fod.mif csffod_norm.mif -mask ../../dti/mask.mif 
chmod a+rwx ./wmfod_norm.mif > /dev/null 2>&1
chmod a+rwx ./csffod_norm.mif > /dev/null 2>&1

# 2) Prepare mask of streamline seeding at grey/white matter boundary
#    Take the 5tt image which was coregistered to the diffusion space. 

## convert nii.gz to mif
mrconvert -force ../../t2/Labels/5tt_reg_to_dwi.nii.gz 5tt_regtodwi.mif 
chmod a+rwx ./5tt_regtodwi.mif > /dev/null 2>&1

    if [[ "$seeding" == "GMWM" ]]; then
    
    # create whitematter-greymatter boundery mask 
    5tt2gmwmi -force 5tt_regtodwi.mif gmwmSeed_reg.mif 
    chmod a+rwx ./gmwmSeed_reg.mif > /dev/null 2>&1
    
    # 3) Create streamlines
    #    Probabilistic tractography with 10 Mio streamlines
    
    tckgen -force -act 5tt_regtodwi.mif -backtrack -seed_gmwmi gmwmSeed_reg.mif -select $num_tracts wmfod_norm.mif tracks_$((num_tracts/1000000))mio.tck
    chmod a+rwx ./tracks_$((num_tracts/1000000))mio.tck > /dev/null 2>&1
    
    
    elif [[ "$seeding" == "dynamic" ]]; then
    
    tckgen -force -act 5tt_regtodwi.mif -backtrack -seed_dynamic wmfod_norm.mif -select $num_tracts wmfod_norm.mif tracks_$((num_tracts/1000000))mio.tck
    chmod a+rwx ./tracks_$((num_tracts/1000000))mio.tck > /dev/null 2>&1
    
    fi
fi
