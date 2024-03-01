 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 14:14:09 2022

@author: anna speckert


This PIPELINE is made for single shell DTI data and incorporates: 
    - dMRI preprocessing: denoising with DIPY, gibbs unringing (MRrix), slice-
      to-volume eddy current correction (FSL), B1 bias field correction (MRtrix)
      (option to skip preprocessing) 
    - Structural preprocessing: tissue segmentation and 5tt creation 
      (option to use freesurfer output, option to use FSL for 5tt)
    - Tractogram creation (MRtrix): response function estimation, orientation 
      distribution function computation (SSST, SS2T, SS3T), anatomically 
      constrained tractography, SIFT(2) filtering
    - Connecome creration (MRtrix): GM pracellation based on Atlas, connectome creation. 

Use the 'config_dti.json' file to choose your options. 

MAKE SURE THAT ....
 ... you have amended the config file to your needs. 
 ... you´re running the pipeline within the virtual environment 
     (see venv_requirements.txt for requirements; Python version 3.8) 
 ... when providing the 5tt image that it is saved in the subject folder under
     /processing/t2/Labels/5tt_reg_to_dwi.nii.gz and is registered to the subject 
     diffusion space and meets the MRtrix criteria. (5ttcheck command in MRtrix)
 ... when providing a response function (rf) that it must be saved under the current
     working directory /Group/Comparison/responsemean. Depending on the rf,
     save it as response_sing_wm_mean.txt resp. response_threetiss_wm_mean.txt
 ... q- and s-form are identical. If not make them identical (I've used the
     q-form (fslorient -qform2sform xx.nii.gz) 
 ... your environmental variable $PATH has the following softwares added: 
     MRtrix3, ANTs, fsl, MRtrix3Tissue, cuda-8.0, Slicer, c3d, 
     freesurfer (FREESURFER_HOME="/directory", $FREESURFER_HOME/SetUpFreeSurfer.sh, 
     export SUBJECTS_DIR="/directory") 


THE DATA STRUCTURE MUST BE THE FOLLOWING: 
 ... base_dir/subj_id/t2/
                        ./T2_SVRTK.nii.gz # a good anatomical image (no need to be t2)
 ... base_dir/subj_id/dti
                        ./dti.nii.gz (diffusion image)
                        ./bvals # txt file 
                        ./bvecs # txt file 

"""

###################### 
##### LIBRARIES ######
######################
import os
import sys
import subprocess
import json
import time
from pipe_helpers.Denoising_DWI import denoising # Denoising functin from Dipy (autoencoder) 
from pipe_helpers.make_5tt import m_5tt # creates 5tt image from segmenttion output 
from pipe_helpers.registration_reformatted_to_B0_for5tt import reg_5tt_tDWI # regisration of segmented 5tt to dMRI space
from pipe_helpers.registration_freeS_to_B0_for5tt import reg_5ttsurfer_tDWI # registration of freesurfer segmented 5tt to dMRI space
from pipe_helpers.neonatal_parcellation import reg_2_parcellation_improved # registration from atlas t2 to subject t2
from pipe_helpers.neonatal_parcellation import parcellation_2_dwi_improved # transforming label image from atlas to subject space
from pipe_helpers.freesurf_to_5tt import free_2_5tt_anat # creating 5tt from freesurfer in anatomical space
from pipe_helpers.freesurf_to_5tt import fivett_2_dwi # transforming 5tt from anatomical space to dwi space 


###########################
### Loading Config File ###
###########################

with open("config_dti.json", "r") as jsonfile:
    configurations = json.load(jsonfile)
    print("Read of config file successful")


#################################
### DEFINING DATA DIRECTORIES ###
#################################

# Make sure that only subject folders are saved within the data directory

base_dir = configurations["base_dir"]

subjects = [] # list of all the subjects in the base_dir
not_working_subj = [] # list of subject for which did not run through 

for subj in os.listdir(base_dir):    # create list with all subjects  
    subjects.append(subj)
print("There are ", len(subjects), "subjects in your base directory.")


for subj in subjects:   # preprocessing loop
     tic_preprocessing = time.time() 
     print("PREPROCESSING starts for Subject ID: ", subj)

### Make processing directories:
     process_dir = base_dir + "/" + subj + "/processing"
     process_t2_dir = process_dir + "/t2"
     process_dti_dir = process_dir + "/dti"
     process_tract_dir = process_dir + "/tractography"

     subprocess.call(["mkdir", "-m777", process_dir]) # -m777 option makes write permisson for all users
     subprocess.call(["mkdir", "-m777", process_t2_dir])
     subprocess.call(["mkdir", "-m777", process_dti_dir])
     subprocess.call(["mkdir", "-m777", process_tract_dir])
    
if configurations["start"] == "skipDP":
    pass
else:    
    #################################    
    ### DTI PREPROCESSING STEPS ###
    #################################
         
    # 1) DENOISING using "Denoising_DWI.py" with the function "denoising()". 
         # input: subject directory 
         # functionality: uses patch2self autoencoder from dipy
         # output: denoised nii.gz image & png image of a denoised slice. 
    for subj in subjects:   # preprocessing loop
         tic_preprocessing = time.time() 
         print("PREPROCESSING starts for Subject ID: ", subj)    
         if os.path.exists(base_dir + "/" + subj + "/processing/dti/denoising/denoised_patch2self.nii.gz"):
            print("Denoised dti image already exists. Will skip to next step.")
         else:        
            print("Denoising starts now...")
            tic_d = time.time()
            denoising(base_dir + "/" + subj)  
            toc_d = time.time()
            if os.path.exists(base_dir + "/" + subj + "/processing/dti/denoising/denoised_patch2self.nii.gz"):
                print("Denoising took ", toc_d-tic_d, "seconds.")
            else:
                print("Denoising did not work. Image processing will continue with the next subject if there is one.")
                not_working_subj.append([subj, "denoising"])
                continue
    
    # 2) Unringing using MRtrix command mrdegibbs. 
         # input: subject directory of denoised mif image (within this block the nii.gz image gets converted to mif) 
         # functionality: uses mrdegibbs from MRtrix to do gibbs ringing correction
         # output: degibbs.mif  
         if os.path.exists(base_dir + "/" + subj + "/processing/dti/degibbs.mif"):
             print("Unringed dti image already exists. Will skip to next step.")
         else:        
             print("Unringing starts now...")
             tic_gi = time.time()
             subprocess.call(["mrconvert", base_dir +"/" + subj + "/processing/dti/denoising/denoised_patch2self.nii.gz", base_dir + "/" + subj + "/processing/dti/denoising/denoised_patch2self.mif"])
             subprocess.call(["mrdegibbs", base_dir +"/" + subj + "/processing/dti/denoising/denoised_patch2self.mif", base_dir +"/" + subj + "/processing/dti/degibbs.mif"])
             subprocess.call(["chmod", "a+rwx", base_dir +"/" + subj + "/processing/dti/degibbs.mif"])
             toc_gi = time.time()
             if os.path.exists(base_dir + "/" + subj + "/processing/dti/degibbs.mif"):
                 print("Unringing took ", toc_gi-tic_gi, "seconds.")
             else:
                 print("Unringing did not work. Image processing will continue with the next subject if there is one.")
                 not_working_subj.append([subj, "unringing"])
                 continue
    
        
    # ageGroup influences the choise of FSL_basic_preprocessing    
    # 3) MOTION & DISTORTION CORRECTION using FSL_basic_preprocessing_v6.sh
         # input: degibbs image as nii.gz 
         # functionality: uses eddy for motion and distortion correction with within-volume correction (depends on eddy_cuda8.0)
         # output: eddy_images.nii.gz (eddy and motion corrected images)
         if os.path.exists(base_dir + "/" + subj + "/processing/dti/eddy_images.mif"):
             print("Eddy image already exists. Will skip to next step.")
         else:      
             print("The next step is motion and distortion correction including within-volume correction.")
             tic_c = time.time()
             subprocess.call(["mrconvert", "-force", base_dir +"/" + subj + "/processing/dti/degibbs.mif", base_dir + "/" + subj + "/processing/dti/degibbs.nii.gz"])
             subprocess.call(["chmod", "a+rwx", base_dir +"/" + subj + "/processing/dti/degibbs.nii.gz"])         
             subprocess.call(["./pipe_helpers/FSL_basic_preprocessing_agegroup_degibbsed.sh", base_dir +"/" + subj, configurations["ageGroup"]]) 
             toc_c = time.time()
             if os.path.exists(base_dir +"/" + subj + "/processing/dti/eddy_images.nii.gz"):
                 print("Eddy images were created. It took ", toc_c-tic_c, "seconds.")
             else:
                 print("Eddy images could not be created. Image processing will continue with the next subject if there is one.")
                 not_working_subj.append(subj)
                 continue
    # Here one could add the eddy quality controL
        
    # 4) B1 bias field correction using MRtrix command dwibias correct ants. 
         # input: subject directory of eddy mif image (within this block the nii.gz image gets converted to mif) 
         # functionality: uses dwibiascorrect ants from MRtrix to do correct for itnensity modulations
         # output: corrected image (biascorr.mif) and the estimated bias field image (biasfield.mif)
         if os.path.exists(base_dir + "/" + subj + "/processing/dti/biascorr.mif"):
             print("B1 bias field corrected dti image already exists. Will skip to next step.")
         else:        
             print("B1 bias field correction starts now...")
             tic_bias = time.time()
             subprocess.call(["mrconvert", "-force", base_dir +"/" + subj + "/processing/dti/eddy_images.nii.gz", base_dir + "/" + subj + "/processing/dti/eddy_images.mif", "-fslgrad", base_dir + "/" + subj + "/dti/bvecs", base_dir + "/" + subj + "/dti/bvals"])
             subprocess.call(["chmod", "a+rwx", base_dir +"/" + subj + "/processing/dti/eddy_images.mif"])
             subprocess.call(["dwibiascorrect", "ants", base_dir +"/" + subj + "/processing/dti/eddy_images.mif", base_dir +"/" + subj + "/processing/dti/biascorr.mif", "-bias", base_dir +"/" + subj + "/processing/dti/biasfield.mif"])
             subprocess.call(["chmod", "a+rwx", base_dir +"/" + subj + "/processing/dti/biascorr.mif"])
             toc_bias = time.time()
             if os.path.exists(base_dir + "/" + subj + "/processing/dti/biascorr.mif"):
                 print("B1 bias field correction took ", toc_bias-tic_bias, "seconds.")
             else:
                 print("B1 bias field correction did not work. Image processing will continue with the next subject if there is one.")
                 not_working_subj.append([subj, "B1 bias field correction"])
                 continue
    
    
    # 5) In the single subject pipeline for SSST the global intensity normalisation is done now.     
         # input: subject directory of bias corrected mif image
         # functionality: uses dwinormalise from MRtrix to do global intensity normalisation
         # output: normalised image (bias_normcorr.mif) 
         if configurations["pipe_kind"] == "single_subject_alone":
             if configurations["rfe"] == "SSST":
                 if os.path.exists(base_dir + "/" + subj + "/processing/dti/bias_normcorr.mif"):
                     print("The global intensity corrected image already exists. Will skip to next step.")
                 else:        
                     print("Global intensity normalisation starts now...")
                     tic_norm2 = time.time()
                     subprocess.call(["dwinormalise", "individual", base_dir + "/" + subj + "/processing/dti/biascorr.mif", base_dir + "/" + subj + "/processing/dti/hifi_nodif_brain_mask.mif", base_dir + "/" + subj + "/processing/dti/bias_normcorr.mif"])
                     subprocess.call(["chmod", "a+rwx", base_dir +"/" + subj + "/processing/dti/bias_normcorr.mif"])
                     toc_norm2 = time.time()
                     if os.path.exists(base_dir + "/" + subj + "/processing/dti/bias_normcorr.mif"):
                         print("Global intensity normalisation took ", toc_norm2-tic_norm2, "seconds.")
                     else:
                         print("Global intensity normalisation did not work. Image processing will continue with the next subject if there is one.")
                         not_working_subj.append([subj, "Global intensity normalisation"])
                         continue
    ### The mask computed during edddy correction (hifi_nodif_brain_mask.nii.gz) will be used.  
    
         toc_preprocessing = time.time()
         print("Preprocessing for subject ", subj, "took ", toc_preprocessing-tic_preprocessing, "seconds.")
    
         
    # 6) This step is only neccessary when comparing groups: Global intensity normalisation across subjects 
         # input: (1) directory with all biascorrected images & (2) directory with brain masks
         # functionality: uses dwinormalise group to perform intenstiy normalisation 
         # output: GroupComparison folder, corrected image (biascorr.mif) and the estimated bias field image (biasfield.mif)
    wor_dir = sys.path[0]
    
    if configurations["pipe_kind"] != "single_subject_alone": 
    
        if configurations["rfe"] == "SSST": # for SS3T and SS2T mtnormalise will be run on FODs. Therefore, this step is not neccessary.  
            if os.path.exists(wor_dir + "/GroupComparison/dwinormalise/"):
                print("The GroupComparison/dwi_normalise folder already exists in the working directory.")
            else:        
                print("Global intensity normalisation for group comparison starts now. Creating folders...")
                tic_bias = time.time()
                # Create directories
                subprocess.call(["mkdir", "-p", "-m777", wor_dir + "/GroupComparison"])
                subprocess.call(["mkdir", "-p", "-m777", wor_dir + "/GroupComparison/dwinormalise"])
                subprocess.call(["mkdir", "-p", "-m777", wor_dir + "/GroupComparison/dwinormalise/dwi_input"])
                subprocess.call(["mkdir", "-p", "-m777", wor_dir + "/GroupComparison/dwinormalise/mask_input"])       
                     
            # # # Copy dwi and mask images to folders
            if os.path.exists(wor_dir + "/GroupComparison/dwinormalise/fa_template_wm_mask.mif"):
                print("The global intensity normalisation for wm was already performed. Will skip to the next step.")
            else:   
                for subj in os.listdir(base_dir):    # go through all subject in the base_dir
                      print("Global intensity normalisation starts for Subject ID: ", subj)
                      subj_dir = base_dir + "/" + subj
                      subprocess.call(["cp", base_dir + "/" + subj + "/processing/dti/biascorr.mif", wor_dir + "/GroupComparison/dwinormalise/dwi_input/" + subj + ".mif"])
                      subprocess.call(["cp", base_dir + "/" + subj + "/processing/dti/hifi_nodif_brain_mask.mif", wor_dir + "/GroupComparison/dwinormalise/mask_input/" + subj + "_mask.mif"])
                         
            #     # group normalisation
                tic_gin = time.time()
                subprocess.call(["dwinormalise", "group", "-force", wor_dir + "/GroupComparison/dwinormalise/dwi_input", wor_dir + "/GroupComparison/dwinormalise/mask_input", wor_dir + "/GroupComparison/dwinormalise/dwi_output/", wor_dir + "/GroupComparison/dwinormalise/fa_template.mif", wor_dir + "/GroupComparison/dwinormalise/fa_template_wm_mask.mif", "-fa_threshold", "0.15"])
                toc_gin = time.time()         
                        
                if os.path.exists(wor_dir + "/GroupComparison/dwinormalise/dwi_output"):
                    print("Global intensity normalisation took ", toc_gin-tic_gin, "seconds.")
                else:
                    print("Global intensity normalisation did not work. Image processing will continue with the next subject if there is one.")
    
    
    # Creating text file with subjects who did not run through preprocessing 
    
    if len(not_working_subj) > 0: 
        # Create text file containing all subjects who did not run through the pipeline
        textfile = open("notWorking_subj.txt", "w")
        for element in not_working_subj:
            textfile.write(element + "\n")
        textfile.close()
        print("The subjects for which the preprocessing did not run through were the following: ", not_working_subj)
    
    # eventually, this needs to be back intended for SSST
    user_answer_dti_preproc = input("\n\n\nBefore continuing with the pipeline, please check the diffusion preprocessed results and \nhave a look at the 'notWorking_subj_preprocessing.txt' which is outputtet in the current working directory. \nIf everything is fine and you want to continue the execution of the pipline press 'y', else press 'n'. \n")
    if user_answer_dti_preproc == "y":
        print("The preprocessed diffusion results seem to be fine. The pipeline goes on..")
        pass
    else:
        print("The execution of the pipeline was stopped.")
        exit()

#%%    
###############################    
### T2 PREPROCESSING STEPS  ###
###############################
             
segmentation_atlas_path = configurations["seg_atlas_path"]
if configurations["5tt_provided"] == "no":
    print("No ready to use 5tt image was provided. It must be created.")

    if configurations["ageGroup"] == "newborn": 
        for subj in subjects:   
             print(" T2 PREPROCESSING starts for Subject ID: ", subj)             
        # 1) REFORMATTING of the super-resolution reconstructed images using chd_to_mmc_network_reformat_anna_cs5.sh
             # input: super-resolution reconstructed T2 image (T2_SVRTK.nii.gz)
             # functionality: in order to be able to run the T2 through the segmentation U-net, it needs this reformatting
             # output: T2_SVRTk_reformatted.nii.gz (reformatted image)
             print("Now the processing of T2 images starts in order to segment them..")     
             if os.path.exists(base_dir + "/" + subj + "/processing/t2/T2_SVRTK_reformatted.nii.gz"):
                 print("T2_SVRTK_reformatted image already exists. Will skip to next step.")  
             else: 
                 print("The SVRTK images are getting reformatted... ")
                 tic_re = time.time()
                 os.chdir(sys.path[0])
                 subprocess.call(["./pipe_helpers/chd_to_mmc_network_reformat_anna_cs5.sh", base_dir +"/" + subj + "/t2/T2_SVRTK.nii.gz", segmentation_atlas_path]) 
                 toc_re = time.time()
                 if os.path.exists(base_dir + "/" + subj + "/processing/t2/T2_SVRTK_reformatted.nii.gz"):
                     print("Reformatting took ", toc_re-tic_re, "seconds. Please check if the reformatting worked out. \n Otherwise use instead of 'chd_to_mmc_network_reformat_anna_cs5.sh' the script 'chd_to_mmc_network_reformat_anna_cs5_new.sh' which uses 12 DOF or 'chd_to_mmc_network_reformat_anna_cs5_new_B.sh' which registeres to other reformatted image.")
                 else:
                     print("Reformatting did not work. Image processing will continue with the next subject if there is one.")
                     not_working_subj.append(subj)
                     continue
        
            
        # 2) SEGMENTATION of the reformatted image using neonatal_segmentation_single_file_probabilityLabels.py
             # input: reformatted super-resolution T2 image
             # functionality: segments T2 in 8 labels 
             # output: t2_labeled and 8 separate label files within label folder 
             if os.path.exists(base_dir + "/" + subj + "/processing/t2/T2_SVRTK_reformatted_labels.nii.gz"):
                 print("Segmented T2 image to create the 8 labels already exists. Will skip to next step.") 
             else:          
                 print("Segmentation to create 8 labels starts now..")
                 tic_s = time.time()
                 subprocess.call(["./pipe_helpers/neonatal_segmentation_single_file_probabilityLabels.py", base_dir + "/" + subj + "/processing/t2/T2_SVRTK_reformatted.nii.gz"]) 
                 toc_s = time.time()
                 if os.path.exists(base_dir + "/" + subj + "/processing/t2/T2_SVRTK_reformatted_labels.nii.gz"):
                     print("Segmentation and creation of 8 labels are done within ", toc_s-tic_s, "seconds.")
                 else:
                     print("Segmentation did not work. Image processing will continue with the next subject if there is one.")
                     not_working_subj.append(subj)
                     continue
                
        
             
        ########################       
        ### ACT PREPARATIONS ###
        ########################
                     
        # 1) CREATE 5-TISUE-TYPE (5TT) IMAGE using make_5tt.py with the function m_5tt() 
             # input: subject directory
             # functionality: based on 8 separate label files, the 5tt image for ACT is created 
             # output: 5tt image (and additional intermediate steps) within label folder
             if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt.nii.gz"):
                 print("The 5tt image already exists. Will skip to next step.") 
             else:                
                 print("The 5tt image will be created for MRtrix usage.. ")
                 tic_5 = time.time()
                 m_5tt(base_dir +"/" + subj + "/") 
                 toc_5 = time.time()
                 if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt.nii.gz"):
                     print("The 5tt creation took ", toc_5-tic_5, "seconds.")
                 else: 
                     print("The 5tt creation did not work. Image processing will continue with the next subject if there is one.")
                     not_working_subj.append(subj)
                     continue
                
        # 2) REGISTRATION of 5tt image to the diffusion space using registration_reformatted_to_B0_for5tt.py with the function reg_5tt_tDWI()
             # input: subject directory
             # functionality: 1) non-linear registration (SyN from ANTS) of T2_reformatted to diffusion space (using skull-stripped b0 image)
             #                2) apply transformation matrix to 5tt using interpolator multiLabel 
             # output: 5tt registred image to the diffusion space (5tt_reg_to_dwi.nii.gz)
             if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt_reg_to_dwi.nii.gz"):
                 print("The 5tt was already registered to the diffusion space. Will skip to next step.") 
             else:               
                 print("The registration of the 5tt image to the diffusion space starts.. ")
                 tic_r = time.time()
                 reg_5tt_tDWI(base_dir +"/" + subj + "/") 
                 toc_r = time.time()
                 if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt_reg_to_dwi.nii.gz"):
                     print("The registration of the 5tt image to the diffusion space took ", toc_r-tic_r, "seconds.")
                 else:
                     print("The registration did not work. Image processing will continue with the next subject if there is one.")
                     not_working_subj.append(subj)
                     continue       
    
    elif (configurations["ageGroup"] == "child")  or (configurations["ageGroup"] == "adolescent"):
        for subj in subjects:
        # 1) Using Freesurfer the Segmentation is created and based on that the 5tt.mif (within segmentation_child_ado.sh)  
        # input: base_dir, subj
        # functionality: 1) Using freesurfer, the nii.gz gets converted to mgz, and the segmenation is computed
        #                2) Based on the segemnted output file, the mrtrix command 5ttgen creates the 5tt image
        # output: 5tt.mif image which is still in the subject structural space
            if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt.mif"):
                print("5tt.mif in T2 space already exists. Will skip to next step.")  
            else: 
                print("5tt creation for the age group ", configurations["ageGroup"], "of subject ", subj, "starts now.. ")
                tic_re = time.time()
                subprocess.call(["./pipe_helpers/segmentation_child_ado.sh", base_dir, subj, configurations["structural_type"]]) 
                toc_re = time.time()
                if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt.mif"):
                    print("5tt Creation took ", toc_re-tic_re, "seconds.")
                else:
                    print("5tt creation did not work. Image processing will continue with the next subject if there is one.")
                    not_working_subj.append(subj)
                    continue

        # 2) REGISTRATION of 5tt image to the diffusion space using registration_freeS_to_B0_for5tt.py with the function reg_5ttsurfer_tDWI()
             # input: subject directory
             # functionality: 1) non-linear registration (SyN from ANTS) of T2 to diffusion space (using skull-stripped b0 image)
             #                2) apply transformation matrix to 5tt using interpolator multiLabel 
             # output: 5tt registred image to the diffusion space (5tt_reg_to_dwi.nii.gz)
            if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt_reg_to_dwi.nii.gz"):
                 print("The 5tt was already registered to the diffusion space. Will skip to next step.") 
            else:               
                 print("The registration of the 5tt image to the diffusion space starts.. ")
                 tic_r = time.time()
                 reg_5ttsurfer_tDWI(base_dir +"/" + subj + "/") 
                 toc_r = time.time()
                 if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt_reg_to_dwi.nii.gz"):
                     print("The registration of the 5tt image to the diffusion space took ", toc_r-tic_r, "seconds.")
                 else:
                     print("The registration did not work. Image processing will continue with the next subject if there is one.")
                     not_working_subj.append(subj)
                     continue  
    
    elif configurations["ageGroup"] == "fetus":
        print("5tt creation for the age group 'fetus' has not yet been implemented.")  
    
    else:
        print("Please provide valid value for config key 'ageGroup'. Choose between: fetus, newborn, child, adolscent.")
    
    user_answer_5tt=input("\n\n\nPlease check the created 5tt_reg_to_dwi.nii.gz. \nIf they look fine and you want to continue the pipeline press 'y', otherwise 'n'.\n")
    if user_answer_5tt == "y":
        print("Pipeline will continue..")
    else:
        print("Pipeline will stop.")
        exit() 
        
elif configurations["5tt_provided"] == "yes":
    if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt_reg_to_dwi.nii.gz"):
        print("The 5tt registered to the diffusion space exists.")
    else: 
        print("The 5tt does not exist under /processing/t2/Labels/. Please provide a 5tt image registered to the diffusion space in this directory or change the variable '5tt_provided' in the config file.")

elif configurations["5tt_provided"] == "genFSL":
    for subj in subjects: 
        if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt_reg_to_dwi.nii.gz"):
            print("The 5tt registered to the diffusion space exists.")
        else: 
            tic = time.time()
            print("The 5tt creation based on fsl segmentation starts now for subject: ", subj)
            subprocess.call(["mkdir", "-m777", "-p", base_dir + "/" + subj + "/processing/t2/Labels/"])
            subprocess.call(["5ttgen", "fsl", base_dir + "/" + subj + "/t2/orig_T1.nii.gz", base_dir + "/" + subj + "/processing/t2/Labels/5tt.nii.gz"]) # you can add the mask already if output is bad 
            subprocess.call(["mrconvert", base_dir + "/" + subj + "/processing/t2/Labels/5tt.nii.gz", base_dir + "/" + subj + "/processing/t2/Labels/5tt.mif"])
            fivett_2_dwi(base_dir, subj)
            toc = time.time()
            if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt_reg_to_dwi.nii.gz"):
                print(subj, ": The 5tt was successfully registered to the diffusion space within .", toc - tic, "seconds.")
                
            else:
                print("The 5tt image could not be created based on freesurfer.")
    user_answer_5tt=input("\n\n\nPlease check the created 5tt_reg_to_dwi.nii.gz. \nIf they look fine and you want to continue the pipeline press 'y', otherwise 'n'.\n")
    if user_answer_5tt == "y":
        print("Pipeline will continue..")
    else:
        print("Pipeline will stop.")
        exit()


elif configurations["5tt_provided"] == "freesurfer":
    for subj in subjects: 
        if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt_reg_to_dwi.nii.gz"):
            print("The 5tt registered to the diffusion space exists.")
        else: 
            tic = time.time()
            print("The 5tt creation based on freesurfer segmentation starts now: ")
            free_2_5tt_anat(base_dir, subj, configurations["freesurfer_version"])
            fivett_2_dwi(base_dir, subj)
            toc = time.time()
            if os.path.exists(base_dir + "/" + subj + "/processing/t2/Labels/5tt_reg_to_dwi.nii.gz"):
                print("The 5tt was successfully registered to the diffusion space within .", toc - tic, "seconds.")
                
            else:
                print("The 5tt image could not be created based on freesurfer.")
    user_answer_5tt=input("\n\n\nPlease check the created 5tt_reg_to_dwi.nii.gz. \nIf they look fine and you want to continue the pipeline press 'y', otherwise 'n'.\n")
    if user_answer_5tt == "y":
        print("Pipeline will continue..")
    else:
        print("Pipeline will stop.")
        exit()



#%%        
#############################################        
### ANATOMICALLY CONSTRAINED TRACTOGRAPHY ###
#############################################
# 0) CHANGE TO WORKING DIRECTORY of the script: 
os.chdir(sys.path[0])

# 1) RESPONSE FUNCTION ESTIMATION 
script_directory= os.getcwd()

if configurations["pipe_kind"] == "single_subject_alone":
    if configurations["rfe"]=="SSST":
        dirs_respf_sing = [] # list of response functions for all subject for single-tissue
        for subj in subjects:   
           if os.path.exists(base_dir + "/" + subj + "/processing/tractography/single_tissue/response_wm_tournier.txt"):
                print("The Fiber orientation estimation with Tournier was already created for ", subj, ". Will skip to next step.") 
           else: 
                print("RESPONSE FUNCTION ESTIMATION starts for Subject ID: ", subj)    
                tic_ft = time.time()
                subprocess.call(["./pipe_helpers/rfe.sh", base_dir +"/" + subj, configurations["rfe"], configurations["pipe_kind"], subj, script_directory]) 
                toc_ft = time.time()
                dirs_respf_sing.append(base_dir + "/" + subj + "/processing/tractography/single_tissue/response_wm_tournier.txt")
                if os.path.exists(base_dir + "/" + subj + "/processing/tractography/single_tissue/response_wm_tournier.txt"):
                    print("Fiber orientation estimation with Tournier took ", toc_ft-tic_ft, "seconds.")
                else:
                    print("The fiber orientation estimation did not work. Image processing will continue with the next subject if there is one.")
                    not_working_subj.append(subj)
    elif configurations["rfe"]=="SS3T":       
         dirs_respf_wm_threetiss = [] # list of response functions for all subject for wm for three-tissue 
         dirs_respf_gm_threetiss = [] # list of response functions for all subject for gm for three-tissue 
         dirs_respf_csf_threetiss = [] # list of response functions for all subject for csf for three-tissue
         for subj in subjects:   
            if os.path.exists(base_dir + "/" + subj + "/processing/tractography/three_tissue/response_wm.txt"):
                print("The Fiber orientation estimation with Dhollander was already created for ", subj, ". Will skip to next step.") 
            else:  
                print("RESPONSE FUNCTION ESTIMATION starts for Subject ID: ", subj)    
                tic_ft = time.time()
                subprocess.call(["./pipe_helpers/rfe.sh", base_dir +"/" + subj, configurations["rfe"], configurations["pipe_kind"], subj, script_directory]) 
                toc_ft = time.time()
                dirs_respf_wm_threetiss.append(base_dir + "/" + subj + "/processing/tractography/three_tissue/response_wm.txt")
                dirs_respf_gm_threetiss.append(base_dir + "/" + subj + "/processing/tractography/three_tissue/response_gm.txt")
                dirs_respf_csf_threetiss.append(base_dir + "/" + subj + "/processing/tractography/three_tissue/response_csf.txt")
                if os.path.exists(base_dir + "/" + subj + "/processing/tractography/three_tissue/response_wm.txt"):
                    print("Fiber orientation estimation with Dhollander took ", toc_ft-tic_ft, "seconds.")
                else:
                    print("The fiber orientation estimation did not work. Image processing will continue with the next subject if there is one.")
                    not_working_subj.append(subj)
    elif configurations["rfe"]=="SS2T":
         dirs_respf_wm_twotiss = [] # list of response functions for all subject for wm for two-tissue 
         dirs_respf_csf_twotiss = [] # list of response functions for all subject for csf for two-tissue    
         for subj in subjects:   
            if os.path.exists(base_dir + "/" + subj + "/processing/tractography/two_tissue/response_wm.txt"):
                print("The Fiber orientation estimation with Dhollander was already created for ", subj, ". Will skip to next step.") 
            else:  
                print("RESPONSE FUNCTION ESTIMATION starts for Subject ID: ", subj)    
                tic_ft = time.time()
                subprocess.call(["./pipe_helpers/rfe.sh", base_dir +"/" + subj, configurations["rfe"], configurations["pipe_kind"], subj, script_directory]) 
                toc_ft = time.time()
                dirs_respf_wm_twotiss.append(base_dir + "/" + subj + "/processing/tractography/two_tissue/response_wm.txt")
                dirs_respf_csf_twotiss.append(base_dir + "/" + subj + "/processing/tractography/two_tissue/response_csf.txt")
                if os.path.exists(base_dir + "/" + subj + "/processing/tractography/two_tissue/response_wm.txt"):
                    print("Fiber orientation estimation with Dhollander took ", toc_ft-tic_ft, "seconds.")
                else:
                    print("The fiber orientation estimation did not work. Image processing will continue with the next subject if there is one.")
                    not_working_subj.append(subj)    
    else:
         print("The configuration varibale 'rfe' is not set. Please do so.")
         
if configurations["pipe_kind"] == "group_create_average":
    if configurations["rfe"]=="SSST":
        dirs_respf_sing = [] # list of response functions for all subject for single-tissue
        for subj in subjects:   
            print("RESPONSE FUNCTION ESTIMATION starts for Subject ID: ", subj)    
            tic_ft = time.time()
            subprocess.call(["./pipe_helpers/rfe.sh", base_dir +"/" + subj, configurations["rfe"], configurations["pipe_kind"], subj, script_directory]) 
            toc_ft = time.time()
            dirs_respf_sing.append(base_dir + "/" + subj + "/processing/tractography/single_tissue/response_wm_tournier.txt")
            if os.path.exists(base_dir + "/" + subj + "/processing/tractography/single_tissue/response_wm_tournier.txt"):
                print("Fiber orientation estimation with Tournier took ", toc_ft-tic_ft, "seconds.")
            else:
                print("The fiber orientation estimation did not work. Image processing will continue with the next subject if there is one.")
                not_working_subj.append(subj)
    elif configurations["rfe"]=="SS3T":  
         if os.path.exists(sys.path[0] + "/GroupComparison/responsemean/response_threetiss_wm_mean.txt"):
             print("The Groupmean was already created. Will skip to next step.") 
         else:         
             dirs_respf_wm_threetiss = [] # list of response functions for all subject for wm for three-tissue 
             dirs_respf_gm_threetiss = [] # list of response functions for all subject for gm for three-tissue 
             dirs_respf_csf_threetiss = [] # list of response functions for all subject for csf for three-tissue
             for subj in subjects:   
                print("RESPONSE FUNCTION ESTIMATION starts for Subject ID: ", subj)    
                tic_ft = time.time()
                subprocess.call(["./pipe_helpers/rfe.sh", base_dir +"/" + subj, configurations["rfe"], configurations["pipe_kind"], subj, script_directory]) 
                toc_ft = time.time()
                dirs_respf_wm_threetiss.append(base_dir + "/" + subj + "/processing/tractography/three_tissue/response_wm.txt")
                dirs_respf_gm_threetiss.append(base_dir + "/" + subj + "/processing/tractography/three_tissue/response_gm.txt")
                dirs_respf_csf_threetiss.append(base_dir + "/" + subj + "/processing/tractography/three_tissue/response_csf.txt")
                if os.path.exists(base_dir + "/" + subj + "/processing/tractography/three_tissue/response_wm.txt"):
                    print("Fiber orientation estimation with Dhollander took ", toc_ft-tic_ft, "seconds.")
                else:
                    print("The fiber orientation estimation did not work. Image processing will continue with the next subject if there is one.")
                    not_working_subj.append(subj)
    elif configurations["rfe"]=="SS2T":
         dirs_respf_wm_twotiss = [] # list of response functions for all subject for wm for two-tissue 
         dirs_respf_csf_twotiss = [] # list of response functions for all subject for csf for two-tissue    
         for subj in subjects:   
            print("RESPONSE FUNCTION ESTIMATION starts for Subject ID: ", subj)    
            tic_ft = time.time()
            subprocess.call(["./pipe_helpers/rfe.sh", base_dir +"/" + subj, configurations["rfe"], configurations["pipe_kind"], subj, script_directory]) 
            toc_ft = time.time()
            dirs_respf_wm_twotiss.append(base_dir + "/" + subj + "/processing/tractography/two_tissue/response_wm.txt")
            dirs_respf_csf_twotiss.append(base_dir + "/" + subj + "/processing/tractography/two_tissue/response_csf.txt")
            if os.path.exists(base_dir + "/" + subj + "/processing/tractography/two_tissue/response_wm.txt"):
                print("Fiber orientation estimation with Dhollander took ", toc_ft-tic_ft, "seconds.")
            else:
                print("The fiber orientation estimation did not work. Image processing will continue with the next subject if there is one.")
                not_working_subj.append(subj)         
    else:
         print("The configuration varibale 'rfe' is not set. Please do so.")
 
### GROUP COMPARISON REQUISITES ####         
# In the following section derivates from the analysis in order to be able to do group comparison are computed: 
# Create a folder for that 
wor_dir = sys.path[0]    

# Create an average response function for the single-tissue case
if configurations["pipe_kind"] == "group_create_average":
    if os.path.exists(sys.path[0] + "/GroupComparison/responsemean/"):
        print("The Groupmean was already created. Will skip to next step.") 
    else:         
        subprocess.call(["mkdir", "-m777", wor_dir + "/GroupComparison"])
        subprocess.call(["mkdir", "-m777", wor_dir + "/GroupComparison/responsemean"])
    if configurations["rfe"] == "SSST": 
        if len(subjects) > 15:            
            print("Response functions over the first 15 subjects from SSST are averaged... ")
            subprocess.call(["responsemean", dirs_respf_sing[0], dirs_respf_sing[1], dirs_respf_sing[2], dirs_respf_sing[3], dirs_respf_sing[4], dirs_respf_sing[5], dirs_respf_sing[6], dirs_respf_sing[7], dirs_respf_sing[8], dirs_respf_sing[9], dirs_respf_sing[10],dirs_respf_sing[11], dirs_respf_sing[12], dirs_respf_sing[13], dirs_respf_sing[14], wor_dir + "/GroupComparison/responsemean/response_sing_wm_mean.txt" ])
            if os.path.exists(wor_dir + "/GroupComparison/responsemean/response_sing_wm_mean.txt"):
                print("Response function from SSST was averaged under: ", wor_dir + "/GroupComparison/responsemean/response_sing_wm_mean.txt" )
            else:
                print("Response functions from SSST could not be averaged.")
        else:
            print("Response functions over the first 2 subjects from SSST are averaged... ")
            subprocess.call(["responsemean", dirs_respf_sing[0], dirs_respf_sing[1], wor_dir + "/GroupComparison/responsemean/response_sing_wm_mean.txt" ])
            if os.path.exists(wor_dir + "/GroupComparison/responsemean/response_sing_wm_mean.txt"):
                print("Response function from SSST was averaged under: ", wor_dir + "/GroupComparison/responsemean/response_sing_wm_mean.txt" )
            else:
                print("Response functions from SSST could not be averaged.")
# Create average response function for the three-tissue case
    if configurations["rfe"] == "SS3T": 
        if len(subjects) > 15:
            print("Response functions over first 15 subjects from SS3T are averaged... ")
            subprocess.call(["responsemean", dirs_respf_wm_threetiss[0],  dirs_respf_wm_threetiss[1],  dirs_respf_wm_threetiss[2],  dirs_respf_wm_threetiss[3],  dirs_respf_wm_threetiss[4],  dirs_respf_wm_threetiss[5],  dirs_respf_wm_threetiss[6],  dirs_respf_wm_threetiss[7],  dirs_respf_wm_threetiss[8],  dirs_respf_wm_threetiss[9],  dirs_respf_wm_threetiss[10], dirs_respf_wm_threetiss[11],  dirs_respf_wm_threetiss[12],  dirs_respf_wm_threetiss[13],  dirs_respf_wm_threetiss[14], wor_dir + "/GroupComparison/responsemean/response_threetiss_wm_mean.txt" ])
            subprocess.call(["responsemean", dirs_respf_gm_threetiss[0], dirs_respf_gm_threetiss[1], dirs_respf_gm_threetiss[2], dirs_respf_gm_threetiss[3], dirs_respf_gm_threetiss[4], dirs_respf_gm_threetiss[5], dirs_respf_gm_threetiss[6], dirs_respf_gm_threetiss[7], dirs_respf_gm_threetiss[8], dirs_respf_gm_threetiss[9], dirs_respf_gm_threetiss[10],dirs_respf_gm_threetiss[11], dirs_respf_gm_threetiss[12], dirs_respf_gm_threetiss[13], dirs_respf_gm_threetiss[14], wor_dir + "/GroupComparison/responsemean/response_threetiss_gm_mean.txt" ])
            subprocess.call(["responsemean", dirs_respf_csf_threetiss[0], dirs_respf_csf_threetiss[1], dirs_respf_csf_threetiss[2], dirs_respf_csf_threetiss[3], dirs_respf_csf_threetiss[4], dirs_respf_csf_threetiss[5], dirs_respf_csf_threetiss[6], dirs_respf_csf_threetiss[7], dirs_respf_csf_threetiss[8], dirs_respf_csf_threetiss[9], dirs_respf_csf_threetiss[10],dirs_respf_csf_threetiss[11], dirs_respf_csf_threetiss[12], dirs_respf_csf_threetiss[13], dirs_respf_csf_threetiss[14], wor_dir + "/GroupComparison/responsemean/response_threetiss_csf_mean.txt" ])
            if os.path.exists(wor_dir + "/GroupComparison/responsemean/response_threetiss_csf_mean.txt"):
                print("Response function from SS3T was averaged under: ", wor_dir + "/GroupComparison/responsemean/" )
            else:
                print("Response functions from SS3T could not be averaged.")
        else:
            print("Response functions over first 2 subjects from SS3T are averaged... ")
            subprocess.call(["responsemean", dirs_respf_wm_threetiss[0],  dirs_respf_wm_threetiss[1], wor_dir + "/GroupComparison/responsemean/response_threetiss_wm_mean.txt" ])
            subprocess.call(["responsemean", dirs_respf_gm_threetiss[0], dirs_respf_gm_threetiss[1], wor_dir + "/GroupComparison/responsemean/response_threetiss_gm_mean.txt" ])
            subprocess.call(["responsemean", dirs_respf_csf_threetiss[0], dirs_respf_csf_threetiss[1], wor_dir + "/GroupComparison/responsemean/response_threetiss_csf_mean.txt" ])
            if os.path.exists(wor_dir + "/GroupComparison/responsemean/response_threetiss_csf_mean.txt"):
                print("Response function from SS3T was averaged under: ", wor_dir + "/GroupComparison/responsemean/")
            else:
                print("Response functions from SS3T could not be averaged.")

    if configurations["rfe"] == "SS2T": 
        if len(subjects) > 15:
            print("Response functions over first 15 subjects from SS3T are averaged... ")
            subprocess.call(["responsemean", dirs_respf_wm_twotiss[0],  dirs_respf_wm_twotiss[1],  dirs_respf_wm_twotiss[2],  dirs_respf_wm_twotiss[3],  dirs_respf_wm_twotiss[4],  dirs_respf_wm_twotiss[5],  dirs_respf_wm_twotiss[6],  dirs_respf_wm_twotiss[7],  dirs_respf_wm_twotiss[8],  dirs_respf_wm_twotiss[9],  dirs_respf_wm_twotiss[10], dirs_respf_wm_twotiss[11],  dirs_respf_wm_twotiss[12],  dirs_respf_wm_twotiss[13],  dirs_respf_wm_twotiss[14], wor_dir + "/GroupComparison/responsemean/response_twotiss_wm_mean.txt" ])
            subprocess.call(["responsemean", dirs_respf_csf_twotiss[0], dirs_respf_csf_twotiss[1], dirs_respf_csf_twotiss[2], dirs_respf_csf_twotiss[3], dirs_respf_csf_twotiss[4], dirs_respf_csf_twotiss[5], dirs_respf_csf_twotiss[6], dirs_respf_csf_twotiss[7], dirs_respf_csf_twotiss[8], dirs_respf_csf_twotiss[9], dirs_respf_csf_twotiss[10],dirs_respf_csf_twotiss[11], dirs_respf_csf_twotiss[12], dirs_respf_csf_twotiss[13], dirs_respf_csf_twotiss[14], wor_dir + "/GroupComparison/responsemean/response_twotiss_csf_mean.txt" ])
            if os.path.exists(wor_dir + "/GroupComparison/responsemean/response_twotiss_csf_mean.txt"):
                print("Response function from SS2T was averaged under: ", wor_dir + "/GroupComparison/responsemean/" )
            else:
                print("Response functions from SS2T could not be averaged.")
        else:
            print("Response functions over first 2 subjects from SS3T are averaged... ")
            subprocess.call(["responsemean", dirs_respf_wm_twotiss[0],  dirs_respf_wm_twotiss[1], wor_dir + "/GroupComparison/responsemean/response_twotiss_wm_mean.txt" ])
            subprocess.call(["responsemean", dirs_respf_csf_twotiss[0], dirs_respf_csf_twotiss[1], wor_dir + "/GroupComparison/responsemean/response_twotiss_csf_mean.txt" ])
            if os.path.exists(wor_dir + "/GroupComparison/responsemean/response_twotiss_csf_mean.txt"):
                print("Response function from SS2T was averaged under: ", wor_dir + "/GroupComparison/responsemean/")
            else:
                print("Response functions from SS2T could not be averaged.")

if configurations["pipe_kind"] == "group_take_average":
    print("Make sure that the averaged response function is provided under the working directory $PWD/GroupComparison/responsemean/response_sing_wm_mean.txt or /response_threetiss_wm_mean.txt")
    
if configurations["pipe_kind"] == "single_subject_alone":
    print("This is a single subject pipeline and its output is not comparable to other subjects.")



# 2) CSD computation 
  # input: 1) subject directory, 2) rfe, 3) pipe kind
  # functionality: creates FOD
  # output: FOD
for subj in subjects:
    print("CSD will be computed for Subject ID: ", subj)
    if configurations["rfe"]== "SSST":
        if os.path.exists(base_dir + "/" + subj + "/processing/tractography/single_tissue/wm_tournier_fod.mif"):
            print("FOD was already created. Will skip to next step.")      
        else:
            print("The next step is FOD creation.")
            tic_t10 = time.time()
            subprocess.call(["./pipe_helpers/csd_total_CS5.sh", base_dir +"/" + subj, configurations["rfe"], configurations["pipe_kind"]]) 
            toc_t10 = time.time()
            if os.path.exists(base_dir + "/" + subj + "/processing/tractography/single_tissue/wm_tournier_fod.mif"):
                print("FOD creation took ", toc_t10-tic_t10, "seconds.")
            else:
                print("FOD creation did not work. Image processing will continue with the next subject if there is one.")
                not_working_subj.append(subj)
    elif configurations["rfe"]== "SS3T":
         if os.path.exists(base_dir + "/" + subj + "/processing/tractography/three_tissue/wm_fod.mif"):
             print("FOD was already created. Will skip to next step.")      
         else:
             print("The next step is FOD creation.")
             tic_t10 = time.time()
             subprocess.call(["./pipe_helpers/csd_total_CS5.sh", base_dir +"/" + subj, configurations["rfe"], configurations["pipe_kind"]]) 
             toc_t10 = time.time()
             if os.path.exists(base_dir + "/" + subj + "/processing/tractography/three_tissue/wm_fod.mif"):
                 print("FOD creation took ", toc_t10-tic_t10, "seconds.")
             else:
                 print("FOD creation did not work. Image processing will continue with the next subject if there is one.")
                 not_working_subj.append(subj)

    elif configurations["rfe"]== "SS2T":
         if os.path.exists(base_dir + "/" + subj + "/processing/tractography/two_tissue/wm_fod.mif"):
             print("FOD was already created. Will skip to next step.")      
         else:
             print("The next step is FOD creation.")
             tic_t10 = time.time()
             subprocess.call(["./pipe_helpers/csd_total_CS5.sh", base_dir +"/" + subj, configurations["rfe"], configurations["pipe_kind"]]) 
             toc_t10 = time.time()
             if os.path.exists(base_dir + "/" + subj + "/processing/tractography/two_tissue/wm_fod.mif"):
                 print("FOD creation took ", toc_t10-tic_t10, "seconds.")
             else:
                 print("FOD creation did not work. Image processing will continue with the next subject if there is one.")
                 not_working_subj.append(subj)
    
# 3) SINGLE-SHELL SINGLE-TISSUE (SSST) Tractogram Creation     
if configurations["rfe"] == "SSST": 
    for subj in subjects:   
         print("TRACTOGRAM CREATION starts for Subject ID: ", subj) 
    # 2.a) FOD NORMALISATION and TRACTOGRAM CREATION of SSST data using tractograms_SSST_I.sh
           # input: 1) subject directory, 2) number of tracts for the tractogram (as string)
           # functionality: normalises the FOD, creates GMWM-seeding mask, creates ACT with backtrack option
           # output: tractogram
         os.chdir(sys.path[0])
         n_tract_s = configurations["streamlinesACT"] # number of tracts for the tractogram 
         n_filt = configurations["streamlinesSIFT"] # resulting number of tracts after filtering
         if os.path.exists(base_dir + "/" + subj + "/processing/tractography/single_tissue/tracks_" + str(int(n_tract_s)//1000000) + "mio.tck"):
             print("FOD normalisation and tractogram creation was already created. Will skip to next step.")      
         else:
             print("The next step is FOD normalisation and tractogram creation with", str(int(n_tract_s)//1000000), "Million streamlines for SSST. If you want to change this setting, 'change n_tract_s' in this script.")
             tic_t10 = time.time()
             subprocess.call(["./pipe_helpers/tractograms_SSST_I.sh", base_dir +"/" + subj, n_tract_s, configurations["seeding"]]) # bash script needs two inpusts: directory and number of tracts to be created as string
             toc_t10 = time.time()
             if os.path.exists(base_dir + "/" + subj + "/processing/tractography/single_tissue/tracks_" + str(int(n_tract_s)//1000000) + "mio.tck"):
                 print("FOD normalisation and tractogram creation with", n_tract_s, "streamlines took ", toc_t10-tic_t10, "seconds.")
             else:
                 print("FOD normalisation and tractogram creation did not work. Image processing will continue with the next subject if there is one.")
                 not_working_subj.append(subj)
                 continue              
    
    # 2. b) FILTERING of tractograms with SIFT using sift_filtering_SSST.sh
            # input: 1) subject directory, 2) number of resulting tracts after filtering (as string), 3) original number of total existing tracts (as string)
            # functionality: Filters the connectome according to Smith et al. to decrease biases 
            # output: filtered tractogram containing as many streamlines as the second input says (eg. sift_1mio.tck)
         if configurations["SIFTmeth"] == "sift1":
             if os.path.exists(base_dir + "/" + subj + "/processing/tractography/single_tissue/sift_" + str(int(n_filt)//1000000) + "mio.tck"):
                 print("SIFT was already created. Will skip to next step.")      
             else:   
                 print("The next step is SIFT Filtering of SSST data. The number of resulting streamlines is ",  str(int(n_filt)//1000000), "Million. Otherwise change 'n_filt' in this script.")
                 tic_sifts = time.time()
                 subprocess.call(["./pipe_helpers/sift_filtering_SSST.sh", base_dir +"/" + subj, n_filt, n_tract_s]) 
                 toc_sifts = time.time()
                 if os.path.exists(base_dir + "/" + subj + "/processing/tractography/single_tissue/sift_" + str(int(n_filt)//1000000) + "mio.tck"):
                     print("SIFT filtering resulting in ", n_filt, "tracts took ", toc_sifts-tic_sifts, "seconds.")
                 else:
                     print("The SIFT filtering did not work. Image processing will continue with the next subject if there is one.")
                     not_working_subj.append(subj)
                     continue 
    
# SIFT2 Filtering
         elif configurations["SIFTmeth"] == "sift2":
             if os.path.exists(base_dir + "/" + subj + "/processing/tractography/single_tissue/tck2_weights.txt"):
                 print("SIFT2 was already created. Will skip to next step.")      
             else: 
                 print("The next step is SIFT2 Filtering of SSST data for subject ", subj)
                 tic_siftm = time.time()
                 subprocess.call(["./pipe_helpers/sift2_filtering_SSST.sh", base_dir +"/" + subj, n_filt, n_tract_s]) 
                 toc_siftm = time.time()
                 if os.path.exists(base_dir + "/" + subj + "/processing/tractography/single_tissue/tck2_weights.txt"):
                     print("SIFT2 filtering took ", toc_siftm-tic_siftm, "seconds.")
                 else:
                     print("The SIFT2 filtering did not work. Image processing will continue with the next subject if there is one.")
                     not_working_subj.append(subj)
                     continue 
    

    print("The tractogram creation for ", subj, "is done.") 
       



# 3) SINGLE-SHELL THREE-TISSUE (SS3T) Tractogram Creation 
if configurations["rfe"] == "SS3T": 
    for subj in subjects: 
       print("TRACTOGRAM CREATION starts for subject ID ", subj)
# 3.a) FOD NORMALISATION and TRACTOGRAM CREATION of SSMT data using tractograms_SSMT.sh
       # input: 1) subject directory, 2) number of tracts for the tractogram (as string)
       # functionality: normalises the FODs, creates GMWM-seeding mask, creates ACT with backtrack option
       # output: tractogram
       os.chdir(sys.path[0])   
       n_tract_m = configurations["streamlinesACT"] # number of tracts for the tractogram
       n_filt_m = configurations["streamlinesSIFT"] # resulting number of tracts after filtering  
       if os.path.exists(base_dir + "/" + subj + "/processing/tractography/three_tissue/tracks_" + str(int(n_tract_m)//1000000) + "mio.tck"):
           print("FOD normalisation and tractogram creation was already created. Will skip to next step.")      
       else:
           print("The next step is FOD normalisation and tractogram creation with", str(int(n_tract_m)//1000000), "Million streamlines for SSMT. If you want to change this setting, change 'n_tract_m' in this script.")
           tic_tm10 = time.time()
           subprocess.call(["./pipe_helpers/tractograms_SSMT.sh", base_dir +"/" + subj, n_tract_m, configurations["seeding"]]) 
           toc_tm10 = time.time()
           if os.path.exists(base_dir + "/" + subj + "/processing/tractography/three_tissue/tracks_" + str(int(n_tract_m)//1000000) + "mio.tck"):
               print("FOD normalisation and tractogram creation with", n_tract_m, "streamlines took ", toc_tm10-tic_tm10, "seconds.")
           else:
               print("FOD normalisation and tractogram creation did not work. Image processing will continue with the next subject if there is one.")
               not_working_subj.append(subj)
               continue 

# 3. b) FILTERING of tractograms with SIFT using sift_filtering_SSMT.sh
        # input: 1) subject directory, 2) number of resulting tracts after filtering (as string), 3) original number of total existing tracts (as string)
        # functionality: Filters the connectome according to Smith et al. to decrease biases 
        # output: filtered tractogram containing as many streamlines as the second input says (eg. sift_1mio.tck)
       if configurations["SIFTmeth"] == "sift1": 
           if os.path.exists(base_dir + "/" + subj + "/processing/tractography/three_tissue/sift_" + str(int(n_filt_m)//1000000) + "mio.tck"):
               print("SIFT was already created. Will skip to next step.")      
           else:        
               print("The next step is SIFT Filtering of SSMT data. The number of resulting streamlines is ",  str(int(n_filt_m)//1000000), "Million. Otherwise change 'n_filt_m' in this script.")
               tic_siftm = time.time()
               subprocess.call(["./pipe_helpers/sift_filtering_SSMT.sh", base_dir +"/" + subj, n_filt_m, n_tract_m]) 
               toc_siftm = time.time()
               if os.path.exists(base_dir + "/" + subj + "/processing/tractography/three_tissue/sift_" + str(int(n_filt_m)//1000000) + "mio.tck"):
                   print("SIFT filtering resulting in ", n_filt_m, "tracts took ", toc_siftm-tic_siftm, "seconds.")
               else:
                   print("The SIFT filtering did not work. Image processing will continue with the next subject if there is one.")
                   not_working_subj.append(subj)
                   continue 

    # SIFT2 Filtering
       elif configurations["SIFTmeth"] == "sift2": 
           if os.path.exists(base_dir + "/" + subj + "/processing/tractography/three_tissue/tck2_weights.txt"):
               print("SIFT2 was already created. Will skip to next step.")      
           else:
               print("The next step is SIFT2 Filtering of SSMT data for subject ", subj)
               tic_siftm = time.time()
               subprocess.call(["./pipe_helpers/sift2_filtering_SSMT.sh", base_dir +"/" + subj, n_filt_m, n_tract_m]) 
               toc_siftm = time.time()
               if os.path.exists(base_dir + "/" + subj + "/processing/tractography/three_tissue/tck2_weights.txt"):
                   print("SIFT2 filtering took ", toc_siftm-tic_siftm, "seconds.")
               else:
                   print("The SIFT2 filtering did not work. Image processing will continue with the next subject if there is one.")
                   not_working_subj.append(subj)
                   continue 

       print("The tractogram creation for ", subj, "is done.")

# 3) SINGLE-SHELL TWO-TISSUE (SS2T) Tractogram Creation 
if configurations["rfe"] == "SS2T": 
    for subj in subjects: 
       print("TRACTOGRAM CREATION starts for subject ID ", subj)
# 3.a) FOD NORMALISATION and TRACTOGRAM CREATION of SSMT data using tractograms_SSMT.sh
       # input: 1) subject directory, 2) number of tracts for the tractogram (as string)
       # functionality: normalises the FODs, creates GMWM-seeding mask, creates ACT with backtrack option
       # output: tractogram
       os.chdir(sys.path[0])   
       n_tract_m = configurations["streamlinesACT"] # number of tracts for the tractogram
       n_filt_m = configurations["streamlinesSIFT"] # resulting number of tracts after filtering  
       if os.path.exists(base_dir + "/" + subj + "/processing/tractography/two_tissue/tracks_" + str(int(n_tract_m)//1000000) + "mio.tck"):
           print("FOD normalisation and tractogram creation was already created. Will skip to next step.")      
       else:
           print("The next step is FOD normalisation and tractogram creation with", str(int(n_tract_m)//1000000), "Million streamlines for SSMT. If you want to change this setting, change 'n_tract_m' in this script.")
           tic_tm10 = time.time()
           subprocess.call(["./pipe_helpers/tractograms_SSMT_topup.sh", base_dir +"/" + subj, n_tract_m, configurations["seeding"], configurations["rfe"]]) 
           toc_tm10 = time.time()
           if os.path.exists(base_dir + "/" + subj + "/processing/tractography/two_tissue/tracks_" + str(int(n_tract_m)//1000000) + "mio.tck"):
               print("FOD normalisation and tractogram creation with", n_tract_m, "streamlines took ", toc_tm10-tic_tm10, "seconds.")
           else:
               print("FOD normalisation and tractogram creation did not work. Image processing will continue with the next subject if there is one.")
               not_working_subj.append(subj)
               continue 

# 3. b) FILTERING of tractograms with SIFT using sift_filtering_SSMT.sh
        # input: 1) subject directory, 2) number of resulting tracts after filtering (as string), 3) original number of total existing tracts (as string)
        # functionality: Filters the connectome according to Smith et al. to decrease biases 
        # output: filtered tractogram containing as many streamlines as the second input says (eg. sift_1mio.tck)
       if configurations["SIFTmeth"] == "sift1": 
           if os.path.exists(base_dir + "/" + subj + "/processing/tractography/two_tissue/sift_" + str(int(n_filt_m)//1000000) + "mio.tck"):
               print("SIFT was already created. Will skip to next step.")      
           else:        
               print("The next step is SIFT Filtering of SSMT data. The number of resulting streamlines is ",  str(int(n_filt_m)//1000000), "Million. Otherwise change 'n_filt_m' in this script.")
               tic_siftm = time.time()
               subprocess.call(["./pipe_helpers/sift_filtering_SSMT_topup.sh", base_dir +"/" + subj, n_filt_m, n_tract_m, configurations["rfe"]]) 
               toc_siftm = time.time()
               if os.path.exists(base_dir + "/" + subj + "/processing/tractography/two_tissue/sift_" + str(int(n_filt_m)//1000000) + "mio.tck"):
                   print("SIFT filtering resulting in ", n_filt_m, "tracts took ", toc_siftm-tic_siftm, "seconds.")
               else:
                   print("The SIFT filtering did not work. Image processing will continue with the next subject if there is one.")
                   not_working_subj.append(subj)
                   continue 

    # SIFT2 Filtering
       elif configurations["SIFTmeth"] == "sift2": 
           if os.path.exists(base_dir + "/" + subj + "/processing/tractography/two_tissue/tck2_weights.txt"):
               print("SIFT2 was already created. Will skip to next step.")      
           else:
               print("The next step is SIFT2 Filtering of SSMT data for subject ", subj)
               tic_siftm = time.time()
               subprocess.call(["./pipe_helpers/sift2_filtering_SSMT_topup.sh", base_dir +"/" + subj, n_filt_m, n_tract_m, configurations["rfe"]]) 
               toc_siftm = time.time()
               if os.path.exists(base_dir + "/" + subj + "/processing/tractography/two_tissue/tck2_weights.txt"):
                   print("SIFT2 filtering took ", toc_siftm-tic_siftm, "seconds.")
               else:
                   print("The SIFT2 filtering did not work. Image processing will continue with the next subject if there is one.")
                   not_working_subj.append(subj)
                   continue 

       print("The tractogram creation for ", subj, "is done.")


if len(not_working_subj) > 0: 
    # Create text file containing all subjects who did not run through the pipeline
    textfile = open("notWorking_subj.txt", "w")
    for element in not_working_subj:
        textfile.write(element + "\n")
    textfile.close()
    print("The subjects for which the processing did not run through were the following: ", not_working_subj)
else:
    print("All subject ran through the tractography steps.")



user_answer_act = input("\n\n\nBefore continuing with the pipeline, please check the tractography results. \nIf everything is fine and you want to continue the execution of the pipline with the \nparcellation according to the Atlas you have defined in the config file, press 'y', else press 'n'. \n")
if user_answer_act == "y":
    print("The tractography results seem to be fine. The pipeline goes on..")
    pass
else:
    print("The execution of the pipeline was stopped.")
    exit()



##############################################        
### PARCELLATION & CONNECTOME CONSTRUCTION ###
##############################################
if configurations["parcellationMethod"] != "none": 
    atlas_name = configurations["parcellationMethod"]
    atlas_t2 = configurations["parcellation_t2"]
    atlas_label_image = configurations["parcellation_labels"]
    
    # Parcellation & Registration of Atlas Parcellation to Subject Diffusion Space 
    for subj in subjects:
        data_dir = base_dir + "/" + subj
        if os.path.exists(base_dir + "/" + subj + "/processing/t2/Parcellation/" + atlas_name + "/T2_parcellated_" + atlas_name + ".nii.gz"):
            print("Subject ", subj, "was already parcellated in t2")
        else:
            print("Subject ", subj, "gets parcellated now in the subject t2 space.")		
            reg_2_parcellation_improved(data_dir, atlas_name, atlas_t2, atlas_label_image)
            if os.path.exists(base_dir + "/" + subj + "/processing/t2/Parcellation/" + atlas_name + "/T2_parcellated_" + atlas_name + ".nii.gz"):
                print("Subject was succesfully parcellated in t2")
            else:
                print("Subject could not be parcellated in t2") 
        if os.path.exists(base_dir + "/" + subj + "/processing/connectome/" + atlas_name + "/parcels_" + atlas_name +"_coreg.nii.gz"):
            print("Label image was already parcellated in the subject ", subj, "dwi space.")
        else:
            subprocess.call(["mkdir", "-m777","-p", base_dir + "/" + subj + "/processing/connectome/" + atlas_name])
            T2_parcellated = base_dir + "/" + subj + "/processing/t2/Parcellation/" + atlas_name + "/T2_parcellated_" +atlas_name+".nii.gz"		
            parcellation_2_dwi_improved(data_dir, T2_parcellated, atlas_name, configurations["ageGroup"]) 
            if configurations["parcellationMethod"] == "ENA33_improved":
                subprocess.call(["./pipe_helpers/corrENA33.sh", base_dir, subj])
            else:
                subprocess.call(["mrconvert", base_dir + "/" + subj + "/processing/connectome/" + atlas_name + "/parcels_" + atlas_name +"_coreg.nii.gz", base_dir + "/" + subj + "/processing/connectome/" + atlas_name + "/nodes.mif"])
                subprocess.call(["chmod", "a+rwx", base_dir + "/" + subj + "/processing/connectome/" + atlas_name +  "/nodes.mif"])
            if os.path.exists(base_dir + "/" + subj + "/processing/connectome/" + atlas_name + "/nodes.mif"):
                print("Label image in subject diffusion space for subject ", subj, "was successfully created in the connectome folder.")
            else:
                print("Label image for subject ", subj, "could not be created. Check if parcellation in subject t2 space exists.") 
else:
    for subj in subjects:
        # here one can add the steps for transformation of Hui's parcellation for MRtrix. 
        # beware that it depends on ENA33 atlas. 
        subprocess.call(["mkdir", "-m777","-p", base_dir + "/" + subj + "/processing/connectome/" + configurations["parcellationName"]])
    print("You have selected that no parcellation should be performed. \nTo be able to create connectomes, make sure that the parcellation you provide is in line with the MRtrix3 requirements. \nSave the parcellation in the subject diffusion space under /subj/processing/connectome/", configurations["parcellationName"], "as .mif format and call the label image 'nodes.mif'.")




###########################
### Connectome Creation ###
###########################

user_answer_parc = input("\n\n\nBefore continuing with the pipeline, please check the parcellation results. \nIf everything is fine and you want to continue the execution of the pipline with the \nconnectome creation based on the weighted sum of streamlines, press 'y', else press 'n'. \n")
if user_answer_parc== "y":
    print("The parcellation results seem to be fine. The pipeline goes on..")
    pass
else:
    print("The execution of the pipeline was stopped.")
    exit()


for subj in subjects:
    print("SUBJECT ID: ", subj)
    if configurations["parcellationMethod"] != "none": 
        if os.path.exists(base_dir + "/" + subj + "/processing/connectome/" + configurations["parcellationMethod"] + "/connectome.csv"):
            print("Connectome from ", configurations["parcellationMethod"], "already exists.")
        else:
            print("Connectome creation from ", configurations["parcellationMethod"], "starts...")
            subprocess.call(["tck2connectome", base_dir + "/" + subj + "/processing/tractography/three_tissue/tracks_" + str(int(n_tract_m)//1000000) + "mio.tck", base_dir + "/" + subj + "/processing/connectome/" + configurations["parcellationMethod"] + "/nodes.mif", base_dir + "/" + subj + "/processing/connectome/" + configurations["parcellationMethod"] + "/connectome.csv", "-tck_weights_in", base_dir + "/" + subj + "/processing/tractography/three_tissue/tck2_weights.txt", "-out_assignments", base_dir + "/" + subj + "/processing/connectome/" + configurations["parcellationMethod"] + "/assignments.txt", "-zero_diagonal", "-assignment_radial_search", "4"])
            if os.path.exists(base_dir + "/" + subj + "/processing/connectome/" + configurations["parcellationMethod"] + "/connectome.csv"):
                print("Connectome was created for subject ", subj, ".")
            else:
                print("Connectome could not be created for subject ", subj, ".")
    else: # individual parcellation already provided
        if os.path.exists(base_dir + "/" + subj + "/processing/connectome/" + configurations["parcellationName"] + "/connectome.csv"):
            print("Connectome from ", configurations["parcellationName"], "already exists.")
        else:
            print("Connectome creation from ", configurations["parcellationName"], "starts...")
            subprocess.call(["tck2connectome", base_dir + "/" + subj + "/processing/tractography/three_tissue/tracks_" + str(int(n_tract_m)//1000000) + "mio.tck", base_dir + "/" + subj + "/processing/connectome/" + configurations["parcellationName"] + "/nodes.mif", base_dir + "/" +subj + "/processing/connectome/" + configurations["parcellationName"] + "/connectome.csv", "-tck_weights_in", base_dir + "/" + subj + "/processing/tractography/three_tissue/tck2_weights.txt", "-out_assignments", base_dir + "/" + subj + "/processing/connectome/" + configurations["parcellationName"] + "/assignments.txt", "-zero_diagonal", "-assignment_radial_search", "4"])
            if os.path.exists(base_dir + "/" + subj + "/processing/connectome/" + configurations["parcellationName"] + "/connectome.csv"):
                print("Connectome was created for subject ", subj, ".")
            else:
                print("Connectome could not be created for subject ", subj, ".")
    

