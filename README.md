# Structural Connectome Pipeline

![pipeline](https://github.com/annspe/connectome_pipeline/assets/98952324/7abf45f9-6992-43f0-b475-7d86e7c9e582)

This pipeline creates structural connectomes based on single-shell diffusion MR images (dMRI) and good resolution structural images. It’s applicable for neonatal, school-age or adolescent data and it includes the following steps: 


__Preprocessing dMRI:__


  *	denoising (DIPY) 

  
  *	gibbs unringing (MRrix)
  
  
  *	slice-to-volume eddy current correction (FSL)
  
  
  *	B1 bias field correction (MRtrix) 




__Structural preprocessing:__ 

  
  *	Neonatal tissue segmentation (based on inhouse UNet algorithm by Kelly Payette, or option to use FSL or Freesurfer output)
  
  
  *	5-tissue-type (5tt) creation 




__Tractogram creation (MRtrix):__ 

  
  *	response function estimation
  
  
  *	orientation distribution fonction (ODF) computation (SSST, SS2T, SS3T)
  
  
  *	anatomically constrained tractography (ACT) , SIFT(2) filtering




__Connecome creration (MRtrix):__ 

  
  *	GM parcellation based on an atlas
  
  
  *	connectome creation




# Contributors:
__Anna Speckert:__ main author, pipeline implementation 


__Kelly Payette:__ neonatal segmentation algorithm 




# Prerequisites to use the pipeline: 
* The following software need to be added to your environmental variable $PATH: MRtrix3, ANTs, fsl, MRtrix3Tissue, cuda-8.0, Slicer, c3d
    * If you'll use freesurfer for segmentation, you need to add freesurfer: freesurfer (FREESURFER_HOME="/directory", FREESURFER_HOME/SetUpFreeSurfer.sh, export SUBJECTS_DIR="/directory") 
*	Create a virtual environment based on the requirements saved in  requirements_venv1.txt (works in Python 3.8) 


# Running the pipeline: 
  *	Save the following in your working directory: ‘DTI_Pipeline.py’, ‘config_dti.json’, ‘pipe_helpers’, ‘resized_atlas_39_t2_h_padded.nii.gz’
  *	Fill out the ‘config_dti.json’ to your needs. 
  *	Have the following data structure of your images you’d like to process and name the files like this: 


   	 ... <base_dir>/<subj_id>/t2


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




# Citations:


* Pipeline is described in: [todo]



__Software included in this pipeline:__
* Avants, B. B., Tustison, N., & Johnson, H. (2014). Advanced Normalization Tools (ANTS) Release 2.x. https://brianavants.wordpress.com/2012/04/13/updated-ants-compile-instructions-april-12-2012/
* Dhollander, T., Clemente, A., Singh, M., Boonstra, F., Civier, O., Duque, J. D., Egorova, N., Enticott, P., Fuelscher, I., Gajamange, S., Genc, S., Gottlieb, E., Hyde, C., Imms, P., Kelly, C., Kirkovski, M., Kolbe, S., Liang, X., Malhotra, A., … Caeyenberghs, K. (2021). Fixel-based Analysis of Diffusion MRI: Methods, Applications, Challenges and Opportunities. In NeuroImage (Vol. 241). Academic Press Inc. https://doi.org/10.1016/j.neuroimage.2021.118417
* Dhollander, T., Mito, R., Raffelt, D., & Connelly, A. (2019, May). Improved white matter response function estimation for 3-tissue constrained spherical deconvolution. Proc. Intl. Soc. Mag. Reson. Med (Vol. 555, No. 10).
* Fadnavis, S., Batson, J., & Garyfallidis, E. (2020). Patch2Self: Denoising Diffusion MRI with Self-Supervised Learning.
* Smith, R. E., Tournier, J.-D., Calamante, F., & Connelly, A. (2012). Anatomically-constrained tractography: Improved diffusion MRI streamlines tractography through effective use of anatomical information. NeuroImage, 62(3), 1924–1938. https://doi.org/10.1016/j.neuroimage.2012.06.005
* Smith, R. E., Tournier, J.-D., Calamante, F., & Connelly, A. (2015). SIFT2: Enabling dense quantitative assessment of brain white matter connectivity using streamlines tractography. NeuroImage, 119, 338–351. https://doi.org/10.1016/j.neuroimage.2015.06.092
* Smith, S. M., Jenkinson, M., Woolrich, M. W., Beckmann, C. F., Behrens, T. E. J., Johansen-Berg, H., Bannister, P. R., De Luca, M., Drobnjak, I., Flitney, D. E., Niazy, R. K., Saunders, J., Vickers, J., Zhang, Y., De Stefano, N., Brady, J. M., & Matthews, P. M. (2004). Advances in functional and structural MR image analysis and implementation as FSL.
* Tournier, J.-D., Calamante, F., & Connelly, A. (2010). Improved probabilistic streamlines tractography by 2nd order integration over fibre orientation distributions. Proceedings of the International Society for Magnetic Resonance in Medicine, 1670.
* Tournier, J.-D., Smith, R., Raffelt, D., Tabbara, R., Dhollander, T., Pietsch, M., Christiaens, D., Jeurissen, B., Yeh, C.-H., & Connelly, A. (2019). MRtrix3: A fast, flexible and open software framework for medical image processing and visualisation. NeuroImage, 202, 116137. https://doi.org/10.1016/j.neuroimage.2019.116137
* Tustison, N. J., Avants, B. B., Cook, P. A., Zheng, Y., Egan, A., Yushkevich, P. A., & Gee, J. C. (2010). N4ITK_Improved_N3_Bias_Correction. IEE Transaction on Medical Imaging, 29(6), 1310–1320.

