#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri 30 Sept 11:40:09 2022

@author: anna speckert
"""
import os
import subprocess
import ants

def free_2_5tt_anat(base_dir, subj, free_ver): 
   # import os
  #  import subprocess
        # Create 5tt.mif from freesurfer parcellation 
    if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt.mif"):
        print("5tt image in structural space already exists for subject ", subj)
    else:
        print("5tt image creating starts now for subject ", subj) 
        subprocess.call(["mkdir", "-m777", base_dir + "/" + subj + "/processing/t2/Labels"])
        subprocess.call(["5ttgen", "freesurfer", base_dir + "/" + subj + "/t2/aparc+aseg.mgz", base_dir + "/" + subj + "/processing/t2/Labels/5tt.mif", "-lut",  "/opt/freesurfer/freesurfer" + free_ver + "/FreeSurferColorLUT.txt"])
        if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt.mif"):
            print("5tt image was created for subject ", subj, "within the anatomical space.")
        else:
            subprocess.call(["5ttgen", "freesurfer", base_dir + "/" + subj + "/t2/aseg.mgz", base_dir + "/" + subj + "/processing/t2/Labels/5tt.mif", "-lut",  "/opt/freesurfer/freesurfer" + free_ver + "/FreeSurferColorLUT.txt"])
            if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt.mif"):
                print("5tt image was created for subject ", subj, "within the anatomical space.")
            else: 
                print("5tt image could not be created for subject ", subj)


def fivett_2_dwi(base_dir, subj):
    # registration! 
   # import ants
    if os.path.exists(base_dir + "/" + subj  + "/processing/t2/Labels/5tt_reg_to_dwi.nii.gz"):
        print("5tt image was already registered to diffusion space.")
    else:

        print("Now the registration from the anatomical space to the diffusion space starts..")
        fixed = ants.image_read(base_dir + "/" + subj + "/processing/dti/hifi_nodif_brain.nii.gz") # skull stripped b0 image 
        moving = ants.image_read(base_dir + "/" + subj  + "/t2/T2_SVRTK.nii.gz") 
        tx = ants.registration(fixed = fixed, moving = moving, type_of_transform = "SyN")
        warped_moving = tx["warpedmovout"]
    # warped_moving.to_filename(base_dir + "/" + subj + "/processing/t2/Labels/t2_regtodwi.nii.gz")
    # subprocess.call(["chmod", "a+rwx", base_dir + "/" + subj  + "/processing/t2/Labels/t2_regtodwi.nii.gz"])    
        print("Registration: Structural to diffusion space done.") # Until here it seemes to work
        
        #To apply this transformation matrix to other images: use ants.applytransform() command:
        
        print("Now the Tranformation on the 5tt image starts...") 
        subprocess.call(["mrconvert", base_dir + "/" + subj + "/processing/t2/Labels/5tt.mif", base_dir + "/" + subj + "/processing/t2/Labels/5tt.nii.gz"])
        moving2 = ants.image_read(base_dir + "/" + subj  + "/processing/t2/Labels/5tt.nii.gz")
        mywarpedimage = ants.apply_transforms(fixed = fixed, moving = moving2, transformlist = tx["fwdtransforms"], interpolator = "nearestNeighbor", imagetype = 3) # nearestNeighbor before multiLabel  (3 stands for time series). 
        # interpolator "multiLabel": fast
        # interpolator "genericLabel": takes a long time. 
        
        mywarpedimage.to_filename(base_dir + "/" + subj + "/processing/t2/Labels/5tt_reg_to_dwi.nii.gz")
        subprocess.call(["chmod", "a+rwx", base_dir + "/" + subj  + "/processing/t2/Labels/5tt_reg_to_dwi.nii.gz"])    
        
        print("Transformation of 5tt image to diffusion space is done.")