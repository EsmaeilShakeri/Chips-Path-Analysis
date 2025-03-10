# -*- coding: utf-8 -*-
"""Chips Analysis .ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15LEGNSj-QA7rTZGhbZAF6vx66Vr8nGws

--------------------------------------------------------------------------------
#### Collaborators Esmaeil Shakeri, Mahmoud Khalghollah
#### Chips Analysis
####Winter  2024

**In this study we are going to detect the Chips path from recorded video that converted to png**

####The following steps are summarized below:
--------------------------------------------------------------------------------

##1- Defining the libraries for the EfficientNetB7 classifcation.
"""

# Commented out IPython magic to ensure Python compatibility.

# Need this to make sure there is no inconsistency
from __future__ import print_function, absolute_import, division, with_statement
import tensorflow as tf
tf.compat.v1.disable_v2_behavior()
!pip install cleanlab

import os
from keras import regularizers
import random
import warnings
import numpy as np
#from __future__ import print_function, absolute_import, division, with_statement
import cleanlab
import numpy as np
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
import warnings
warnings.simplefilter("ignore")
np.random.seed(477)
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.utils import class_weight
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, cohen_kappa_score
from keras.models import Model
from keras import optimizers, applications
from keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import EarlyStopping, ReduceLROnPlateau
from keras.layers import Dense, Dropout, GlobalAveragePooling2D, Input
# %matplotlib inline
sns.set(style="whitegrid")
warnings.filterwarnings("ignore")
import tensorflow as tf
import sklearn

from google.colab import drive
drive.mount('/content/drive')

"""##2- Imported two csv file from training and testing without noisy images"""

# for test I removed some samples by random (not for main code)
n = 1
#test = pd.read_csv("/content/drive/MyDrive/CSV Original classification/test.csv", skiprows=lambda i: i % n != 0)
train = pd.read_csv(".csv", skiprows=lambda i: i % n != 0)
train["pxl_nm"] = train["pxl_nm"].apply(lambda x: x + ".png") #reading data form the folders
#test[""] = test[""].apply(lambda x: x + ".png")
train['Chips_id'] = train['Chips_id'].astype('str')
train['Chips_id'] = train['Chips_id'].apply(lambda x: x if x == '0' else '1') # to make the binary labels
# test[''] = test[''].apply(lambda x: x if x == 0 else 1)

"""##3- Defining the Data generator"""

# defining the parameters and creating the training generator
BATCH_SIZE = 32
EPOCHS = 60
WARMUP_EPOCHS = 2
LEARNING_RATE = 1e-4
WARMUP_LEARNING_RATE = 1e-3
HEIGHT = 556 #please check the size of pixcel
WIDTH = 556
CANAL = 3
N_CLASSES = train['Chips_id'].nunique()
ES_PATIENCE = 5
RLROP_PATIENCE = 3
DECAY_DROP = 0.5
X_train, X_val = train_test_split(train, test_size=0.2, random_state=160)
train_datagen=ImageDataGenerator(rescale=1./255,
                                 rotation_range=360,
                                 horizontal_flip=True,
                                 vertical_flip=True)




train_generator=train_datagen.flow_from_dataframe(
    dataframe=X_train,
    directory="",
    x_col="pxl_nm",
    y_col="Chips_id",
    class_mode="categorical",
    batch_size=BATCH_SIZE,
    target_size=(HEIGHT, WIDTH),
    seed=0)

validation_datagen = ImageDataGenerator(rescale=1./255)

valid_generator=validation_datagen.flow_from_dataframe(
    dataframe=X_val,
    directory="",
    x_col="pxl_nm",
    y_col="Chips_id",
    class_mode="categorical",
    batch_size=BATCH_SIZE,
    target_size=(HEIGHT, WIDTH),
    seed=0)

#test_datagen = ImageDataGenerator(rescale=1./255)

#test_generator = test_datagen.flow_from_dataframe(
    #    dataframe=test,
     #   directory = "",
    #    x_col="",
   #     batch_size=1,
   #     class_mode=None,
   #     shuffle=False,
  #      target_size=(HEIGHT, WIDTH),
  #      seed=0)

#This is just for test to see the inline structure
train_generator.reset()
X,y = next(train_generator)

"""##4- Implementing the EfficientNetB7 architecture  as a pre-train model"""

def pred_model(input_shape, n_out):
    input_tensor = Input(shape=input_shape)
    #base_model = tf.keras.applications.resnet50.ResNet50(weights='imagenet', include_top=False,
    base_model = tf.keras.applications.efficientnet.EfficientNetB7(weights='imagenet', include_top=False,
                                       input_tensor=input_tensor)
    # base_model.load_weights('drive/My Drive/Colab Notebooks/Esmaeil/data/resnet50_weights_tf_dim_ordering_tf_kernels_notop.h5')

    x = GlobalAveragePooling2D()(base_model.output)
    x = Dropout(0.5)(x)
    x = Dense(1048, kernel_regularizer=regularizers.l2(0.01), activation='relu')(x) #please check the total number of images
    x = Dropout(0.5)(x)
    final_output = Dense(n_out, activation='sigmoid', name='final_output')(x)
    model = Model(input_tensor, final_output)

    return model



model = pred_model(input_shape=(HEIGHT, WIDTH, CANAL), n_out=N_CLASSES)

for layer in model.layers:
    layer.trainable = False

for i in range(-5, 0):
    model.layers[i].trainable = True

#Defining class wiehgts for the multi-class issue.
print(np.unique(train['Chips_id'].values))
class_weights = sklearn.utils.class_weight.compute_class_weight('balanced', classes = np.unique(train['Chips_id'].astype('int').values), y=train['Chips_id'].astype('int').values)
# class_weights = class_weight.compute_class_weight('balanced', classes = np.unique(train['diagnosis']), y = train['diagnosis'])
class_weights = dict(enumerate(class_weights))

metric_list = ["accuracy"]
optimizer = tf.keras.optimizers.Adam(lr=WARMUP_LEARNING_RATE)
model.compile(optimizer=optimizer, loss='categorical_crossentropy',  metrics=metric_list)
model.summary()

#earlystopping to make sure model does not work after perfirmace did not change
for layer in model.layers:
    layer.trainable = True

#es = EarlyStopping(monitor='val_loss', mode='min', patience=ES_PATIENCE, restore_best_weights=True, verbose=1)
rlrop = ReduceLROnPlateau(monitor='val_loss', mode='min', patience=RLROP_PATIENCE, factor=DECAY_DROP, min_lr=1e-6, verbose=1)

callback_list =[ rlrop] #[#es, rlrop]
optimizer = tf.keras.optimizers.Adam(lr=LEARNING_RATE)
model.compile(optimizer=optimizer, loss='categorical_crossentropy',  metrics=metric_list)
model.summary()

"""##5- Training and testing the model."""

STEP_SIZE_TRAIN = train_generator.n//train_generator.batch_size
STEP_SIZE_VALID = valid_generator.n//valid_generator.batch_size
history_warmup = model.fit_generator(generator=train_generator,
                                     steps_per_epoch=STEP_SIZE_TRAIN,
                                     validation_data=valid_generator,
                                     validation_steps=STEP_SIZE_VALID,
                                     epochs=WARMUP_EPOCHS,
                                     class_weight=class_weights,
                                     verbose=1).history


history_finetunning = model.fit_generator(generator=train_generator,
                                          steps_per_epoch=STEP_SIZE_TRAIN,
                                          validation_data=valid_generator,
                                          validation_steps=STEP_SIZE_VALID,
                                          epochs=EPOCHS,
                                          callbacks=callback_list,
                                          class_weight=class_weights,
                                          verbose=1).history


history = {'loss': history_warmup['loss'] + history_finetunning['loss'],
           'val_loss': history_warmup['val_loss'] + history_finetunning['val_loss'],
           'acc': history_warmup['acc'] + history_finetunning['acc'],
           'val_acc': history_warmup['val_acc'] + history_finetunning['val_acc']}

sns.set_style("whitegrid")
fig, (ax1, ax2) = plt.subplots(2, 1, sharex='col', figsize=(20, 14))

ax1.plot(history['loss'], label='Train loss')
ax1.plot(history['val_loss'], label='Validation loss')
ax1.legend(loc='best')
ax1.set_title('Loss')

ax2.plot(history['acc'], label='Train acc')
ax2.plot(history['val_acc'], label='Validation acc')
ax2.legend(loc='best')
ax2.set_title('Accuracy')

plt.xlabel('Epochs')
sns.despine()
plt.show()

plt.plot(history['loss'])
plt.plot(history['val_loss'])
plt.title('Model Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')

plt.legend(['Train', 'Validation'], loc='upper left', bbox_to_anchor=(1,1))
plt.show()

plt.plot(history['acc'])
plt.plot(history['val_acc'])
plt.title('Model AUC')
plt.ylabel('AUC')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left', bbox_to_anchor=(1,1))
plt.show()

"""##Confusion matrix"""

# Create empty arays to keep the predictions and labels
lastFullTrainPred = np.empty((0, N_CLASSES))
lastFullTrainLabels = np.empty((0, N_CLASSES))
lastFullValPred = np.empty((0, N_CLASSES))
lastFullValLabels = np.empty((0, N_CLASSES))

# Add train predictions and labels
for i in range(STEP_SIZE_TRAIN+1):
    im, lbl = next(train_generator)
    scores = model.predict(im, batch_size=train_generator.batch_size)
    lastFullTrainPred = np.append(lastFullTrainPred, scores, axis=0)
    lastFullTrainLabels = np.append(lastFullTrainLabels, lbl, axis=0)

# Add validation predictions and labels
for i in range(STEP_SIZE_VALID+1):
    im, lbl = next(valid_generator)
    scores = model.predict(im, batch_size=valid_generator.batch_size)
    lastFullValPred = np.append(lastFullValPred, scores, axis=0)
    lastFullValLabels = np.append(lastFullValLabels, lbl, axis=0)


lastFullComPred = np.concatenate((lastFullTrainPred, lastFullValPred))
lastFullComLabels = np.concatenate((lastFullTrainLabels, lastFullValLabels))
complete_labels = [np.argmax(label) for label in lastFullComLabels]

train_preds = [np.argmax(pred) for pred in lastFullTrainPred]
train_labels = [np.argmax(label) for label in lastFullTrainLabels]
validation_preds = [np.argmax(pred) for pred in lastFullValPred]
validation_labels = [np.argmax(label) for label in lastFullValLabels]

fig, (ax1, ax2) = plt.subplots(1, 2, sharex='col', figsize=(24, 7))
labels = ['0 - Chips', '1 - Non Chips']
train_cnf_matrix = confusion_matrix(train_labels, train_preds)
validation_cnf_matrix = confusion_matrix(validation_labels, validation_preds)

train_cnf_matrix_norm = train_cnf_matrix.astype('float') / train_cnf_matrix.sum(axis=1)[:, np.newaxis]
validation_cnf_matrix_norm = validation_cnf_matrix.astype('float') / validation_cnf_matrix.sum(axis=1)[:, np.newaxis]

train_df_cm = pd.DataFrame(train_cnf_matrix_norm, index=labels, columns=labels)
validation_df_cm = pd.DataFrame(validation_cnf_matrix_norm, index=labels, columns=labels)

sns.heatmap(train_df_cm, annot=True, fmt='.2f', cmap="Blues", ax=ax1).set_title('Train')
sns.heatmap(validation_df_cm, annot=True, fmt='.2f', cmap=sns.cubehelix_palette(8), ax=ax2).set_title('Validation')
plt.show()

"""Sesitivity, Specifity, Percision"""

cohen_kappa_score
