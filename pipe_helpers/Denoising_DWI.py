#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  8 10:44:51 2022

@author: anna
"""
# Denoising with dipy 
import numpy as np
import subprocess
import nibabel as nib 
from dipy.io.image import save_nifti
import matplotlib.pyplot as plt
from dipy.denoise.patch2self import patch2self


def denoising(data_dir):  # where data_dir = base_dir + subj
    nii = nib.load(data_dir + "/dti" +"/dti.nii.gz") 
    affine = nii.affine
    data = nii.get_fdata() # get the actual data 
    
    bvals = np.loadtxt(data_dir + "/dti/bvals")
    denoised_arr = patch2self(data, bvals, model='ols', shift_intensity=True,
                              clip_negative_vals=False, b0_threshold=50)
    
    # Gets the center slice and the middle volume of the 4D diffusion data.
    sli = data.shape[2] // 2
    gra = 21  # pick out a random volume for a particular gradient direction
    
    orig = data[:, :, sli, gra]
    den = denoised_arr[:, :, sli, gra]
    
    # computes the residuals
    rms_diff = np.sqrt((orig - den) ** 2)
    
    fig1, ax = plt.subplots(1, 3, figsize=(12, 6),
                            subplot_kw={'xticks': [], 'yticks': []})
    
    fig1.subplots_adjust(hspace=0.3, wspace=0.05)
    
    ax.flat[0].imshow(orig.T, cmap='gray', interpolation='none',
                      origin='lower')
    ax.flat[0].set_title('Original')
    ax.flat[1].imshow(den.T, cmap='gray', interpolation='none',
                      origin='lower')
    ax.flat[1].set_title('Denoised Output')
    ax.flat[2].imshow(rms_diff.T, cmap='gray', interpolation='none',
                      origin='lower')
    ax.flat[2].set_title('Residuals')
    
    subprocess.call(["mkdir", "-m777", data_dir + "/processing/dti/denoising"])
    
    fig1.savefig(data_dir + '/processing/dti/denoising/denoised_patch2self.png')
    subprocess.call(["chmod", "a+rwx", data_dir + "/processing/dti/denoising/denoised_patch2self.png"])
    print("The result saved in", data_dir +"/processing/dti/denoising/denoised_patch2self.png")
    
    
    save_nifti(data_dir + '/processing/dti/denoising/denoised_patch2self.nii.gz', denoised_arr, affine)
    # new line for chmod
    subprocess.call(["chmod", "a+rwx", data_dir + "/processing/dti/denoising/denoised_patch2self.nii.gz"])
   

    print("Entire denoised data saved in", data_dir +"/processing/dti/denoising/denoised_patch2self.nii.gz")
