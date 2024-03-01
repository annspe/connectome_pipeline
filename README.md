# Structural Connectome Pipeline

![pipeline](https://github.com/annspe/connectome_pipeline/assets/98952324/7abf45f9-6992-43f0-b475-7d86e7c9e582)

This pipeline creates structural connectomes based on single-shell diffusion MR images (dMRI) and good resolution structural images. It’s applicable for neonatal, school-age or adolescent data and it includes the following steps: 


Preprocessing dMRI:


  *	denoising (DIPY) 

  
  *	gibbs unringing (MRrix)
  
  
  *	slice-to-volume eddy current correction (FSL)
  
  
  *	B1 bias field correction (MRtrix) 




Structural preprocessing: 

  
  *	Neonatal tissue segmentation (based on inhouse UNet algorithm by Kelly Payette, or option to use FSL or Freesurfer output)
  
  
  *	5-tissue-type (5tt) creation 




Tractogram creation (MRtrix): 

  
  *	response function estimation
  
  
  *	orientation distribution fonction (ODF) computation (SSST, SS2T, SS3T)
  
  
  *	anatomically constrained tractography (ACT) , SIFT(2) filtering




Connecome creration (MRtrix): 

  
  *	GM parcellation based on an atlas
  
  
  *	connectome creation


# Contributors:
Anna Speckert: main author, pipeline implementation 


Kelly Payette: neonatal segmentation algorithm 


# Prerequisites to use the pipeline: 
* The following software need to be added to your environmental variable $PATH: MRtrix3, ANTs, fsl, MRtrix3Tissue, cuda-8.0, Slicer, c3d
    * If you'll use freesurfer for segmentation, you need to add freesurfer: freesurfer (FREESURFER_HOME="/directory", FREESURFER_HOME/SetUpFreeSurfer.sh, export SUBJECTS_DIR="/directory") 
*	Create a virtual environment based on the requirements saved in  requirements_venv1.txt (works in Python 3.8) 


# Running the pipeline: 
  *	Save the following in your working directory: ‘DTI_Pipeline.py’, ‘config_dti.json’, ‘pipe_helpers’, ‘resized_atlas_39_t2_h_padded.nii.gz’
  *	Fill out the ‘config_dti.json’ to your needs. 
  *	Have the following data structure of your images you’d like to process and name the files like this: 


   	 ... <base_dir>/<subj_id>/t2/


   	                        ./T2_SVRTK.nii.gz # a good anatomical image, not necessarily t2)


   	... <base_dir>/<subj_id>/dti


   	                      ./dti.nii.gz (diffusion image)


   	                      ./bvals # txt file 


   	                      ./bvecs # txt file

  * Make sure that….
      * q- and s-form are identical. If not make them identical (eg. fslorient -qform2sform xx.nii.gz)   
      * when providing the 5tt image that it is saved in the subject folder under /processing/t2/Labels/5tt_reg_to_dwi.nii.gz and is registered to the subject diffusion space and meets the MRtrix criteria. (5ttcheck command in MRtrix)
      *	when providing a response function (rf) that it must be saved under the current working directory /Group/Comparison/responsemean. Depending on the rf, save it as response_sing_wm_mean.txt resp. response_threetiss_wm_mean.txt
      
  * Activate your virtual environment 


  * Run ‘DTI_Pipeline.py’
