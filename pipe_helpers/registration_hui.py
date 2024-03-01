#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 09:29:36 2023

@author: speckert

This script is for Hui to register the T2_SVRTK to the subject diffusion space.
It uses the median of the b0 images for the reigstration. 

"""
import time 
import subprocess
import ants

def reg_T2_dwi(data_dir): 
    
    """" 
    This function registers the T2 image to the diffusion space  
    
    Inputs:
        data_dir = base_dir + subj
    
    Ouput: 
        The registered T2 in the diffusion space.
        If you apply the transformation to another image, this will be outputted too.       
    
    """
    
    print("Registration from subject T2 space to subject dwi space starts..")
    tic=time.time()    
    # Create the median non-b0 image 
    T2 = "..." # add here the path to the T2 
    # creates the median b0
    subprocess.call(["./DTI_pipeline/pipe_helpers/medianB0.sh", data_dir])    
    moving = ants.image_read(T2) # T2 image in atlas space 
    fixed = ants.image_read(data_dir + "/processing/dti/median_bzero.mif") # If you have changed directories in medianB0_hui.sh please als change it here    
    mask = ants.image_read(data_dir + "/processing/dti/hifi_nodif_brain_mask.nii.gz") # enter the path to the binary mask of the dwi image
    tx = ants.registration(fixed = fixed, moving = moving, mask = mask, type_of_transform = "SyN")
    warped_moving = tx["warpedmovout"]
    warped_moving.to_filename(data_dir + "/processing/dti/t2_regtodwi.nii.gz") 
    toc=time.time()
    print("Registration: T2 to dwi done in", toc-tic, "seconds.") 
 