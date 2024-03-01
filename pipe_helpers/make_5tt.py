#!/usr/bin/env python3

# Script which creates the 5tt format from the output of the UNet based on 8 (probability) labels. 
# Make sure that python3 & MRtrix3 are installed

import nibabel as nib # nifti library
import numpy as np
import os 
import subprocess

def m_5tt(data_dir): # data_dir = base_dir + subj
   
    
    # Creates 4D file, where the 8 label probabilities are concatenated along the 4th dimension
    os.chdir(data_dir + "processing/t2/Labels/")
    
    os.system('fslmerge -t all_problabels.nii.gz label_prob_1.nii.gz label_prob_2.nii.gz label_prob_3.nii.gz label_prob_4.nii.gz label_prob_5.nii.gz label_prob_6.nii.gz label_prob_7.nii.gz label_prob_8.nii.gz')
    subprocess.call(["chmod", "a+rwx", data_dir + "processing/t2/Labels/all_problabels.nii.gz"])
    
    print("The 4D label image 'all_problabels.nii.gz' was created. Now the creation of the 5tt/3tt image starts..") 
    
    # Loading the all label image
    #nii = nib.load("all_labels_anna.nii.gz") # this is the nifti file which was created with the old labels. 
    nii = nib.load("all_problabels.nii.gz") # see old_stuff: labels_all.nii.gz (this is the correct image to start from) 
    nii_hdr = nii.header # header info
    affine = nii.affine
    nii_data = nii.get_fdata() # get the actual data 
    
    
    sizex = nii_data.shape[0]
    sizey = nii_data.shape[1]
    sizez = nii_data.shape[2]
    
    # Creates 5 x 3D images per 5tt label. 
    # The numbes in the end are all actual label number -1 because it starts at 0 
    corGM = nii_data[:,:,:,1]
    subcorGM = (nii_data[:,:,:,5]+nii_data[:,:,:,7])
    WM = (nii_data[:,:,:,2] + nii_data[:,:,:,4] + nii_data[:,:,:,6])
    CSF = (nii_data[:,:,:,0] + nii_data[:,:,:,3])
    patho = np.zeros((sizex, sizey, sizez))
    
    
    # Change Dimensions: Because we have 3D images now and no longer 4D 
    newdim = [1, 400, 400, 400, 1, 1, 1, 1]
    nii_hdr["dim"] = newdim # overwrite header
    
    # Before saving the image, one needs to apply the new header
    x_corGM = nib.Nifti1Image(corGM, affine, nii_hdr)
    x_subcorGM = nib.Nifti1Image(subcorGM, affine, nii_hdr)
    x_WM = nib.Nifti1Image(WM, affine, nii_hdr)
    x_CSF = nib.Nifti1Image(CSF, affine, nii_hdr)
    x_patho = nib.Nifti1Image(patho, affine, nii_hdr)
    
    
    #### ACTIVATE THIS PART TO REALLY CREATE THE 3D images
    # Saving the actual nifti files to the label folder
    nib.save(x_corGM, "corGM.nii.gz")
    nib.save(x_subcorGM, "subcorGM.nii.gz")
    nib.save(x_WM, "WM.nii.gz")
    nib.save(x_CSF, "CSF.nii.gz")
    nib.save(x_patho, "patho.nii.gz")
    subprocess.call(["chmod", "a+rwx", data_dir + "processing/t2/Labels/corGM.nii.gz"])
    subprocess.call(["chmod", "a+rwx", data_dir + "processing/t2/Labels/subcorGM.nii.gz"])
    subprocess.call(["chmod", "a+rwx", data_dir + "processing/t2/Labels/WM.nii.gz"])
    subprocess.call(["chmod", "a+rwx", data_dir + "processing/t2/Labels/CSF.nii.gz"])
    subprocess.call(["chmod", "a+rwx", data_dir + "processing/t2/Labels/patho.nii.gz"])
    
    print('Five 3D images per label were created. Now they will be merged together along 4th dimension to a single 4D image...')
    
    # Merging the 3D files along the 4th axis with with FSL (maybe there exists a simple solution with python?)
    os.system('fslmerge -t 5tt_draft.nii.gz corGM.nii.gz subcorGM.nii.gz WM.nii.gz CSF.nii.gz patho.nii.gz') 
    subprocess.call(["chmod", "a+rwx", data_dir + "processing/t2/Labels/5tt_draft.nii.gz"])    
    
    print("A first draft of the 5tt image was created. Now it needs to be corrected so that it meets the MRtrix requirements...") 
    
    # Sum of voxels per label should always be 1 and the rest 0: 
    # Take 5tt image which was created by running fslmerge on the 5 separate 3D files to create 4D file 
    nii5 = nib.load("5tt_draft.nii.gz")
    affine5 = nii5.affine
    nii5_hdr = nii5.header
    nii5_data = nii5.get_fdata()
    
    
    # outside of the brain it should be 0, and the sum within the brain 1 (of label dimension)
    nii5_data[nii5_data < 0.01] = 0
    nii5_data[nii5_data > 0.99] = 1
    
    # Since the image values may or may not take values larger than 1, it does a normalisation to 3D maximum. This should not change anything if the maximum intensity is already 1. 
    for t in range(4):
        nii5_data[:,:,:,t] = np.absolute(nii5_data[:,:,:,t]/np.amax(np.amax(np.amax(nii5_data[:,:,:,t]))))
    
    
    difference = np.ones((sizex, sizey, sizez)) - np.sum(nii5_data, 3)
    CSF_new = nii5_data[:,:,:,3] + (difference * (difference<0.2))
    
    nii5_data = np.stack((nii5_data[:,:,:,0], nii5_data[:,:,:,1], nii5_data[:,:,:,2], CSF_new, nii5_data[:,:,:,4]), axis = 3) # here might have happend a mistake np.stack creates a NEW dimension. Double check Anna! 
    
    summed = np.sum(nii5_data, 3) # shape: (400, 400, 400)
    
    selected = ((summed!=1) & (summed!=0)) # selected = boolean array (shape: 400, 400, 400)
    
    
    selected4D = np.stack((selected, selected, selected, selected, selected), axis = 3)
    nii5_data[selected4D] = 0 
    
    
    x_nii5 = nib.Nifti1Image(nii5_data, affine5, nii5_hdr)
    
    nib.save(x_nii5, "5tt.nii.gz") 
    subprocess.call(["chmod", "a+rwx", data_dir + "processing/t2/Labels/5tt.nii.gz"])    
    print("The '5tt.nii.gz' was created in the labels folder.")
    
    
    print("Now the 5ttcheck command from Mrtrix checks if the 5tt meets the criteria..")
    
    os.system('5ttcheck 5tt.nii.gz')
    
    
