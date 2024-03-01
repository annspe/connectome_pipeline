#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 09:21:31 2022

@author: anna
"""
import ants # pip install antspyx is neccessary1
import time
import subprocess
import os
import sys



def reg_2_parcellation_improved(data_dir, atlas_name, atlas_t2, atlas_label_image): 
    
    """" 
    This function parcellates the T2 image based on the MCRIB parcellation using
    the ENA50 atlas which is directly comparable with the Desikan-Killiany adult brain atlas. 
    
    Inputs:
        data_dir = base_dir + subj
        atlas_name: name of the Atlas (eg. ENA50)
        atlas_t2: directory of the T2 of the Atlas (without skull)
        atlas_label_image: directory of the label image of the Atlas 
    
    Ouput: 
        Within data_dir/processing/t2 a new folder "parcellation" is created with 2 files:
        - The registered atlas t2 image to subject T2 space
        - The label image registered to the subject space
    
    """
    
    print("The following parcellation will rely on the ", atlas_name, " Atlas.")
    print("Registration from Atlas T2 space to subject T2 space starts..")
    tic=time.time()
    moving = ants.image_read(atlas_t2) # T2 image in atlas space 
    fixed = ants.image_read(data_dir + "/t2/T2_SVRTK.nii.gz") # T2 subject space 
    subprocess.call(["fslmaths", data_dir + "/t2/T2_SVRTK.nii.gz", "-bin", data_dir + "/t2/T2_mask.nii.gz"]) 
    print("Please check the just created T2 mask in your t2 directory")
    subprocess.call(["chmod", "a+rwx", data_dir + "/t2/T2_mask.nii.gz"])
    mask = ants.image_read(data_dir + "/t2/T2_mask.nii.gz")
    tx = ants.registration(fixed = fixed, moving = moving, mask = mask, type_of_transform = "SyN")
    warped_moving = tx["warpedmovout"]
    subprocess.call(["mkdir", "-m777", data_dir + "/processing/t2/Parcellation"])
    subprocess.call(["mkdir", "-m777", data_dir + "/processing/t2/Parcellation/" + atlas_name])
    # warped_moving.to_filename(data_dir + "/processing/t2/Parcellation/" + atlas_name + "/" + atlas_name +"_regSubj.nii.gz")
    # subprocess.call(["chmod", "a+rwx", data_dir + "/processing/t2/Parcellation/" + atlas_name + "/" + atlas_name +"_regSubj.nii.gz"])    
    print("Registration: Atlas to SVRTK done.") 
        
    print("Now the Transformation starts: label image on T2... ") 
    moving2 = ants.image_read(atlas_label_image) # label image in the Atlas space
    mywarpedimage = ants.apply_transforms(fixed = fixed, moving = moving2, transformlist = tx["fwdtransforms"], interpolator = "genericLabel")  
    # interpolator "multiLabel": fast
    # interpolator "genericLabel": takes a long time. 
    
    mywarpedimage.to_filename(data_dir + "/processing/t2/Parcellation/" + atlas_name + "/T2_parcellated_" + atlas_name +".nii.gz")
    subprocess.call(["chmod", "a+rwx", data_dir + "/processing/t2/Parcellation/" + atlas_name + "/T2_parcellated_" + atlas_name +".nii.gz"])    
    toc=time.time()
    subprocess.call('rm /tmp/*Warp.nii.gz', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.call('rm /tmp/*Affine.mat', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("Transformation to the parcellation completed in ", toc-tic, "seconds.")


def parcellation_2_dwi_improved(data_dir, T2_parcellated, atlas_name, age_group):
    """" 
    This function registeres the parcellated T2 to the diffusion space with a 
    affine transformation. 
    Inputs:
        data_dir = base_dir + subj
        T2_parcellated: the parcellated image in the T2 subject space
        atlas_name: name of the atlas
    
    Ouput: 
        parcellated image in the diffusion space 
    
    """
    
    print("Registration from subject T2 space to subject diffusion starts..")
    tic=time.time()
    # create median of b0-image
    if age_group == "newborn": 
        subprocess.call([sys.path[0] + "/pipe_helpers/medianB0.sh", data_dir]) # ./DTI_pipeline/pipe_helpers/
        subprocess.call(["mrconvert", data_dir + "/processing/dti/median_bzero.mif", data_dir + "/processing/dti/median_bzero.nii.gz"])
        moving = ants.image_read(data_dir + "/t2/T2_SVRTK.nii.gz") # T2 image in atlas space 
        subprocess.call(["bet", data_dir + "/processing/dti/median_bzero.nii.gz", data_dir + "/processing/dti/median_bzero_bet.nii.gz", "-m", "-f", "0.3"])
        fixed = ants.image_read(data_dir + "/processing/dti/median_bzero_bet.nii.gz") # dwi subject space 
        mask = ants.image_read(data_dir + "/processing/dti/median_bzero_bet_mask.nii.gz") # we are having a too small voxel values problem

    else:
        subprocess.call([sys.path[0] + "/pipe_helpers/median_nonB0.sh", data_dir]) # ./DTI_pipeline/pipe_helpers/
        subprocess.call(["mrconvert", data_dir + "/processing/dti/median_nonbzero.mif", data_dir + "/processing/dti/median_nonbzero.nii.gz"])
        moving = ants.image_read(data_dir + "/t2/T2_SVRTK.nii.gz") # T2 image in atlas space 
        subprocess.call(["bet", data_dir + "/processing/dti/median_nonbzero.nii.gz", data_dir + "/processing/dti/median_nonbzero_bet.nii.gz", "-m", "-f", "0.3"])
        fixed = ants.image_read(data_dir + "/processing/dti/median_nonbzero_bet.nii.gz") # dwi subject space 
        mask = ants.image_read(data_dir + "/processing/dti/median_nonbzero_bet_mask.nii.gz") # we are having a too small voxel values problem


# Registration starts 
    tx1 = ants.registration(fixed = fixed, moving = moving, mask=mask,  type_of_transform = "TRSAA") # must be affine (9df)! mask = mask,
    warped_moving = tx1["warpedmovout"]
    warped_moving.to_filename(data_dir + "/processing/dti/intermediate_image.nii.gz")
    movingb = ants.image_read(data_dir + "/processing/dti/intermediate_image.nii.gz")
    tx2 = ants.registration(fixed = fixed, moving = movingb, mask = mask, type_of_transform = "SyNOnly") # mask = mask,
    tx = tx1["fwdtransforms"] + tx2["fwdtransforms"]
    print("Registration: Subject T2 to subject diffusion space done.") 
        
    print("Now the Transformation starts: label image on T2... ") 
    moving2 = ants.image_read(T2_parcellated) # parcellated image in subject T2 space
    mywarpedimage = ants.apply_transforms(fixed = fixed, moving = moving2, transformlist = tx, interpolator = "genericLabel") #imagetype = 3
    # interpolator "multiLabel": fast
    # interpolator "genericLabel": takes a long time. 
    

    if os.path.exists(data_dir + "/processing/connectome/" + atlas_name):	
    	mywarpedimage.to_filename(data_dir + "/processing/connectome/" + atlas_name +"/parcels_" + atlas_name +"_coreg.nii.gz")        
    	subprocess.call(["chmod", "a+rwx", data_dir + "/processing/connectome/" + atlas_name + "/parcels_" + atlas_name +"_coreg.nii.gz"])    
    else:
        subprocess.call(["mkdir", "-m777", data_dir + "/processing/connectome/" + atlas_name])
        mywarpedimage.to_filename(data_dir + "/processing/connectome/" + atlas_name +"/parcels_" + atlas_name +"_coreg.nii.gz") 
        subprocess.call(["chmod", "a+rwx", data_dir + "/processing/connectome/" + atlas_name + "/parcels_" + atlas_name +"_coreg.nii.gz"]) 
    toc=time.time()
    subprocess.call('rm /tmp/*Warp.nii.gz', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.call('rm /tmp/*Affine.mat', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Transformation of the parcellated image to the diffusion space completed in ", toc-tic, "seconds.")

