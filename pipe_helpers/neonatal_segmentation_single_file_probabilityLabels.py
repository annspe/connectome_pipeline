#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mar 11, 2021

Neonatal Segmentation - no training

Segments into: gm, wm, ext_csf, vent, brainstem, cerebellum, deep gm, hippocampus, not brain
@author: Kelly Payette

script amended by Anna Speckert 
"""

import time
import os
import sys

from medpy.io import load, save
import numpy as np

from keras.models import Model

from keras.layers import Input, Conv2D
from keras.layers import BatchNormalization, Dropout, MaxPooling2D 
from keras.layers import UpSampling2D, Concatenate
from keras.optimizers import Adam
from keras import regularizers
from keras import backend as K

from subprocess import call
import subprocess


cwd = os.getcwd()
ckpt_path = cwd + '/neonate_seg_tf2_v4.h5'

if len(sys.argv) == 1:
	print( "Error:\nPlease specify file to be segmented: neonatal_segmentation.py [t2_file.nii.gz]")
	print("File should have a resolution of 0.4x0.4x0.4mm, with a size of 400x400x400 voxels")
	sys.exit()
else:
	file_t2 = sys.argv[1] # first argument you pass
	print("Current model: " + ckpt_path)
	print("\n")

data_dir = file_t2[:(len(file_t2)-42)] # -42 last letters results in base_dir + subj
t2_path = data_dir + "/t2/" # Anna added this

def padimage(padinput, padoutput, targetsize):
	#PADS files to targetsize 	
	# padinput = input file
	# padoutput = output file
	# targetsize = target number of voxels along each side of cube

	 
	dimensions = list(map(int, subprocess.check_output(['mrinfo', '-size', padinput]).strip().split()))[:3]
	dimensions = np.fromstring(' '.join(str(e) for e in dimensions), dtype=int, sep=' ')
	xdim=dimensions[0]
	ydim=dimensions[1]
	zdim=dimensions[2]
	print(xdim)
	print(ydim)
	print(zdim)
	
	xpad=targetsize - xdim
	ypad=targetsize - ydim
	zpad=targetsize - zdim

	call("c3d " + padinput + " -pad 0x0x0vox " + str(xpad) + "x" + str(ypad) + "x" + str(zpad) + "vox 0 -o " + padoutput, shell=True)


################ Generalized Dice Coefficient Loss ######################
def gen_dice_coef(y_true, y_pred, smooth=1e-7):
    '''
    Dice coefficient for 8 categories. 
    Pass to model as metric during compile statement
    '''
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    weight = 1 / (K.sum(y_true_f))**2
    intersect = K.sum(weight * K.sum(y_true_f * y_pred_f, axis=-1))
    denom = K.sum(weight*K.sum(y_true_f + y_pred_f, axis=-1))
    return K.mean((2. * intersect / (denom + smooth)))

def gen_dice_coef_loss(y_true, y_pred):
    '''
    Dice loss to minimize. Pass to model as loss during compile statement
    '''
    return 1 - gen_dice_coef(y_true, y_pred)


################ Create Model ######################
def unet_architecture(input_img):
	
	conv1 = Conv2D(32, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(input_image)
	conv1 = BatchNormalization()(conv1)
	conv1 = Conv2D(32, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(conv1)
	conv1 = BatchNormalization()(conv1)
	pool1 = MaxPooling2D(pool_size=(2,2))(conv1)
	pool1 = Dropout(0.25)(pool1)
	
	conv2 = Conv2D(64, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(pool1)
	conv2 = BatchNormalization()(conv2)
	conv2 = Conv2D(64, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(conv2)
	conv2 = BatchNormalization()(conv2)
	pool2 = MaxPooling2D(pool_size=(2,2))(conv2)
	pool2 = Dropout(0.5)(pool2)
	
	conv3 = Conv2D(128, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(pool2)
	conv3 = BatchNormalization()(conv3)
	conv3 = Conv2D(128, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(conv3)
	conv3 = BatchNormalization()(conv3)
	pool3 = MaxPooling2D(pool_size=(2,2))(conv3)
	pool3 = Dropout(0.5)(pool3)
	
	conv4 = Conv2D(256, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(pool3)
	conv4 = BatchNormalization()(conv4)
	conv4 = Conv2D(256, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(conv4)
	conv4 = BatchNormalization()(conv4)
	pool4 = MaxPooling2D(pool_size=(2,2))(conv4)
	pool4 = Dropout(0.5)(pool4)
	
	conv5 = Conv2D(512, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(pool4)
	conv5 = BatchNormalization()(conv5)
	conv5 = Conv2D(512, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(conv5)
	conv5 = BatchNormalization()(conv5)
	

	up6 = UpSampling2D(size=(2, 2))(conv5)
	up6 = Concatenate(axis=3)([up6, conv4])
	up6 = Dropout(0.5)(up6)
	conv6 = Conv2D(256, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(up6)
	conv6 = BatchNormalization()(conv6)
	conv6 = Conv2D(256, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(conv6)
	conv6 = BatchNormalization()(conv6)
	
	up7 = UpSampling2D(size=(2, 2))(conv6)
	up7 = Concatenate(axis=3)([up7, conv3])
	up7 = Dropout(0.5)(up7)
	conv7 = Conv2D(128, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(up7)
	conv7 = BatchNormalization()(conv7)
	conv7 = Conv2D(128, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(conv7)
	conv7 = BatchNormalization()(conv7)
	
	up8 = UpSampling2D(size=(2, 2))(conv7)
	up8 = Concatenate(axis=3)([up8, conv2])
	up8 = Dropout(0.5)(up8)
	conv8 = Conv2D(64, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(up8)
	conv8 = BatchNormalization()(conv8)
	conv8 = Conv2D(64, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01))(conv8)
	conv8 = BatchNormalization()(conv8)
	
	up9 = UpSampling2D(size=(2, 2))(conv8)
	up9 = Concatenate(axis=3)([up9, conv1])
	up9 = Dropout(0.5)(up9)
	conv9 = Conv2D(32, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01), name='last_3')(up9)
	conv9 = BatchNormalization()(conv9)
	conv9 = Conv2D(32, kernel_size=(3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01), name='last_2')(conv9)
	conv9 = BatchNormalization()(conv9)

	pred = Conv2D(9, kernel_size=(1,1),  activation='softmax', padding='valid', name='last_1')(conv9)
	final_model = Model(inputs=input_image, outputs=pred)

	return final_model


################ Network Parameters ###################
K.clear_session()
width = 400
height = 400
n_channels = 1
n_classes = 9 # total classes (gm, wm, ext_csf, vent, brainstem, cerebellum, deep gm, hippocampus, not brain)
num_epochs = 200
batch=16
targetsize=400


##############Train Model with Feta Data and save model###################

input_image=Input(shape=(width,height,1))
model = unet_architecture(input_image)
adam = Adam(lr=0.00001)
# load model
print('loading trained model')
model.load_weights(ckpt_path, by_name=True)
print('loaded pre-trained model')

model.compile(optimizer=adam, loss=[gen_dice_coef_loss], metrics=[gen_dice_coef])
#print(model.summary())

t=time.time()
				   
image_data, image_header = load(file_t2) # Load data

image_data = image_data.astype('float')
image_data_new = image_data

for i in range (image_data_new.shape[2]):
	if image_data_new[:,:,i].max() != 0:
		image_data_new[:,:,i] = image_data_new[:,:,i]/(image_data_new[:,:,i].max()) 

imageDim = np.shape(image_data_new)   
image_data_new = np.moveaxis(image_data_new, -1, 0) # Bring the last dim to the first

input_data1 = image_data_new[..., np.newaxis] # Add one axis to the end

out = model.predict(input_data1)
 
_out = np.reshape(out, (imageDim[2], imageDim[1], imageDim[0], n_classes)) # Reshape to input shape
			
# 			print(_out[10:20, 10:20, 10:20,3])
#			Uncomment for one-hot encoding

labels = np.argmax(np.asarray(_out), axis=3).astype(float) # Find mask
labels = np.moveaxis(labels, 0, -1) # Bring the first dim to the last
			
filename = file_t2[:-7]

#### Here Anna's adaptations start to get separate labels from the total label file: ####
os.chdir(data_dir + "/processing/t2")
os.system('mkdir Labels')
os.system('chmod a+rwx ./Labels')

#### ACTIVATE THIS LINE IN ORDER TO CREATE THE REGULAR KELLY SEGMENTATION 
save(labels, filename + '_labels.nii.gz', image_header) # Save the mask
subprocess.call(['chmod', 'a+rwx', filename + '_labels.nii.gz'])

### Here probability labels are created without the arg_max
labels_p = np.asarray(_out).astype(float) # Find mask (from original script)
labels_p = np.moveaxis(labels_p, 0, -2) # Bring the first dim to the SECOND last (TRICK)



label_path = data_dir + '/processing/t2/Labels'
print("The 'Labels' folder was created under: ", label_path)
os.chdir(label_path)

# Creates 1 3D image for every label
for k in range(1,9):
    save(labels_p[:,:,:,k], label_path +"/label_prob_"+str(k)+".nii.gz", image_header)
    subprocess.call(['chmod', 'a+rwx', label_path +'/label_prob_'+str(k)+'.nii.gz'])

elapsed = time.time() - t

print('time elapsed: ' + str(elapsed) + 's')

if os.path.isfile(filename + '_labels.nii.gz'):
	print("Labels created: " + filename + '_labels.nii.gz')
else:
    print("labels were unable to be created")
