#!/usr/bin/env python3

# Performs bias correction (n4) for structural images and 
# registration (ANTS) from structural space (SVRTK) to diffusion space (b0) 



import ants # pip install antspyx is neccessary1
import subprocess


def reg_5tt_tDWI(data_dir): # data_dir = base_dir + subj

    
    # Registration: reformatted_SVRTK to B0 with non-linear transform called "SyN": 
    print("Registration starts..")
    fixed = ants.image_read(data_dir + "processing/dti/hifi_nodif_brain.nii.gz") # skull stripped b0 image 
    moving = ants.image_read(data_dir + "processing/t2/T2_SVRTK_reformatted.nii.gz") 
    tx = ants.registration(fixed = fixed, moving = moving, type_of_transform = "SyN")
    warped_moving = tx["warpedmovout"]
    warped_moving.to_filename(data_dir + "processing/t2/Labels/t2reformatted_regtodwi.nii.gz")
    subprocess.call(["chmod", "a+rwx", data_dir + "processing/t2/Labels/t2reformatted_regtodwi.nii.gz"])    
    print("Registration: reformatted SVRTK to b0 done.") # Until here it seemes to work
    
    #To apply this transformation matrix to other images: use ants.applytransform() command:
    
    print("Now the Tranformation starts...") 
    moving2 = ants.image_read(data_dir + "/processing/t2/Labels/5tt.nii.gz")
    mywarpedimage = ants.apply_transforms(fixed = fixed, moving = moving2, transformlist = tx["fwdtransforms"], interpolator = "multiLabel", imagetype = 3) #   (3 stands for time series). 
    # interpolator "multiLabel": fast
    # interpolator "genericLabel": takes a long time. 
    
    mywarpedimage.to_filename(data_dir + "processing/t2/Labels/5tt_reg_to_dwi.nii.gz")
    subprocess.call(["chmod", "a+rwx", data_dir + "processing/t2/Labels/5tt_reg_to_dwi.nii.gz"])    
    
    print("Transformation of 5tt image to diffusion space is done.")
    
    
