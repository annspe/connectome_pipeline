#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 10 15:51:38 2022

@author: anna
"""
# Registration of freesurfer based 5tt to diffusion 

import ants # pip install antspyx is neccessary1
import subprocess


def reg_5ttsurfer_tDWI(data_dir): # data_dir = base_dir + subj
    
    # assuming that the 5tt is still in the same space as the T2: 
    print("Registration starts..")
    fixed = ants.image_read(data_dir + "processing/dti/hifi_nodif_brain.nii.gz") # skull stripped b0 image 
    moving = ants.image_read(data_dir + "/t2/T2_SVRTK.nii.gz") 
    tx = ants.registration(fixed = fixed, moving = moving, type_of_transform = "SyN")
    warped_moving = tx["warpedmovout"]
    warped_moving.to_filename(data_dir + "processing/t2/Labels/t2_regtodwi.nii.gz")
    subprocess.call(["chmod", "a+rwx", data_dir + "processing/t2/Labels/t2_regtodwi.nii.gz"])    
    print("Registration: SVRTK to B0 done.") # Until here it seemes to work
    
    #To apply this transformation matrix to other images: use ants.applytransform() command:
    
    print("Now the Tranformation starts...") 
    moving2 = ants.image_read(data_dir + "/processing/t2/Labels/5tt.nii.gz")
    mywarpedimage = ants.apply_transforms(fixed = fixed, moving = moving2, transformlist = tx["fwdtransforms"], interpolator = "multiLabel", imagetype = 3) # nearestNeighbor, before here was multiLabel  (3 stands for time series). 
    # interpolator "multiLabel": fast
    # interpolator "genericLabel": takes a long time. 
    
    mywarpedimage.to_filename(data_dir + "processing/t2/Labels/5tt_reg_to_dwi.nii.gz")
    subprocess.call(["chmod", "a+rwx", data_dir + "processing/t2/Labels/5tt_reg_to_dwi_linear.nii.gz"])    
    
    print("Transformation of 5tt image to diffusion space is done.")
    
