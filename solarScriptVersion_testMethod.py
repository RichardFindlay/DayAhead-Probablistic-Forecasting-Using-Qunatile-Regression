import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
import tensorflow.keras
import tensorflow.keras.backend as K
import sys, os
import h5py 

from tensorflow.keras import Model
from tensorflow.keras.layers import Conv1D, Conv2D, Softmax, Bidirectional, Dense, TimeDistributed, LSTM 
from tensorflow.keras.layers import Input, Activation, AveragePooling2D, Lambda, concatenate, Flatten, BatchNormalization, RepeatVector, Permute, Lambda, Dropout
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.layers import Reshape
from tensorflow.keras.callbacks import Callback
from tensorflow.keras.models import load_model
from pickle import dump, load
import time

np.set_printoptions(threshold=sys.maxsize)
tf.random.set_seed(180)


import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation
import seaborn as sns
import random

###########################################_____LOAD_PROCESSED_DATA_____############################################
dataset_name = 'train_set_V11_withtimefeatures_120hrinput.hdf5'

# load training data dictionary
# train_set_load = open("/content/drive/My Drive/Processed_Data/train_set_V6_withtimefeatures_120hrinput_.pkl", "rb") 
# train_set = load(train_set_load)
# train_set_load.close()

# print train_set data shapes
# for key in train_set.keys():
# 	print(f'{key}: {train_set[key].shape}')

# get size parameters
f = h5py.File(f"/content/drive/My Drive/Processed_Data/{dataset_name}", "r")
features = np.empty_like(f['train_set']['X1_train'][0])
times_in = np.empty_like(f['train_set']['X2_train'][0])
times_out = np.empty_like(f['train_set']['X3_train'][0])
labels = np.empty_like(f['train_set']['y_train'][0])
x_len = f['train_set']['X1_train'].shape[0]
y_len = f['train_set']['y_train'].shape[0]
print('size parameters loaded')

# print(x_len)
# print(y_len)
# sys.exit()

f.close()


###########################################_____DATA_GENERATOR_____#################################################

params = {'batch_size': 32,
		'shuffle': False } 

class DataGenerator(tensorflow.keras.utils.Sequence):

	def __init__(self, dataset_name, x_length, y_length, batch_size, shuffle):
		self.dataset_name = dataset_name
		self.batch_size = batch_size
		self.shuffle = shuffle
		self.xlen = x_length
		self.ylen = y_length 
		self.input_idx = 0
		self.on_epoch_end()

		self.idx = 0 
		self.idx_count = self.batch_size / 48
		self.previous_idx = 0  
		self.prev_y_true = None    

	def __len__(self):
		# 'number of batches per Epoch'
		return int(np.floor(self.ylen / self.batch_size))

	def __getitem__(self, index):

		# # input batch ref updates 
		# indexes = []

		# while len(indexes) < self.batch_size: 

		# 	if self.previous_idx != 0:
		# 		idxs = [self.idx-1 for x in range(self.previous_idx)]
		# 		indexes.extend(idxs)
		# 		self.idx_count -=  (self.previous_idx / 48)
		# 		self.previous_idx = 0 

		# 	if self.idx_count >= 1:
		# 		for i in range(int(np.floor(self.idx_count))):
		# 			idxs = [self.idx for x in range(48)]
		# 			indexes.extend(idxs)
		# 			self.idx += 1 
		# 			self.idx_count -= 1

		# 	if self.idx_count < 1:
		# 		idx_len = self.idx_count * 48
		# 		idxs = [self.idx for x in range(int(idx_len))]
		# 		indexes.extend(idxs)
		# 		self.idx_count -= (int(idx_len) / 48)

		# 		# how much of the prev index we need to include in the next batch
		# 		if 48 - int(idx_len) < self.batch_size:
		# 			self.previous_idx = 48 - int(idx_len)
		# 		else:
		# 			self.previous_idx = 0

		# 	if np.round(abs(self.idx_count),4) == 0:            
		# 		self.idx += 1
		# 		self.idx_count = self.batch_size / 48 

		# print(indexes)
		# asset index len matches batch size
		# assert len(indexes) == self.batch_size, "batch size and constructed indexes length do not match"

		input_indexes = self.input_indexes[index * self.batch_size:(index+1) * self.batch_size]
		output_indexes = self.output_indexes[index * self.batch_size:(index+1) * self.batch_size]

		# Generate data
		(X_train1, X_train2, X_train3, decoder_input), y_train = self.__data_generation(input_indexes, output_indexes)

		return (X_train1, X_train2, X_train3, decoder_input), (y_train, [], []) # pass empty training outputs to extract extract attentions

	def on_epoch_end(self):
		# set length of indexes for each epoch
		self.input_indexes = []
		self.output_indexes = np.arange(self.ylen)

		# # input batch ref updates 
		# indexes = []
		# previous_idx = 0
		# idx = 0
		# batch_size = 24
		# idx_count = batch_size / 48

		# while len(indexes) < self.ylen: 

		# 	if previous_idx != 0:
		# 		idxs = [idx-1 for x in range(previous_idx)]
		# 		indexes.extend(idxs)
		# 		idx_count -=  (previous_idx / 48)
		# 		previous_idx = 0 

		# 	if idx_count >= 1:
		# 		for i in range(int(np.floor(idx_count))):
		# 			idxs = [idx for x in range(48)]
		# 			indexes.extend(idxs)
		# 			idx += 1 
		# 			idx_count -= 1

		# 	if idx_count < 1:
		# 		idx_len = idx_count * 48
		# 		idxs = [idx for x in range(int(idx_len))]
		# 		indexes.extend(idxs)
		# 		idx_count -= (int(idx_len) / 48)

		# 		# how much of the prev index we need to include in the next batch
		# 		if 48 - int(idx_len) < batch_size:
		# 			previous_idx = 48 - int(idx_len)
		# 		else:
		# 			previous_idx = 0

		# 	if np.round(abs(idx_count),4) == 0:            
		# 		idx += 1
		# 		idx_count = batch_size / 48 


		xlist_idxs = np.arange(self.xlen)
		for idx in xlist_idxs:
			repeat_idx = [idx] * 48 
			self.input_indexes.extend(repeat_idx)     


		if self.shuffle == True:
			np.random.shuffle(self.input_indexes)

	def __data_generation(self, input_indexes, output_indexes):

		# X_train1 = np.empty([features.shape[0], features.shape[1], features.shape[2], features.shape[3]])
		# X_train2 = np.empty((times_in.shape[1], times_in.shape[2]))

		X_train1 = []
		X_train2 = []

		f = h5py.File(f"/content/drive/My Drive/Processed_Data/{self.dataset_name}", "r")    
		for i in input_indexes:        
			X_train1_read = f['train_set']['X1_train'][i]
			X_train2_read = f['train_set']['X2_train'][i]

			X_train1.append(X_train1_read) 
			X_train2.append(X_train2_read)

		X_train1 = np.stack(X_train1, axis=0)
		X_train2 = np.stack(X_train2, axis=0)       

		X_train3 = f['train_set']['X3_train'][output_indexes]
		y_train = f['train_set']['y_train'][output_indexes]

		X_train3 = np.expand_dims(X_train3, axis=1)
		y_train = np.expand_dims(y_train, axis=1)
 

		if self.prev_y_true is not None:
			decoder_input = self.prev_y_true
		else:
			intial_input = np.average(X_train1, axis=(2,3))
			decoder_input = intial_input[:, -48, 0]
			decoder_input = np.expand_dims(decoder_input, axis=1)
			decoder_input = np.expand_dims(decoder_input, axis=-1)

		self.prev_y_true = decoder_input

		f.close()  

		return (X_train1, X_train2, X_train3, decoder_input), y_train

training_generator = DataGenerator(dataset_name = dataset_name, x_length = x_len, y_length = y_len,  **params)


###########################################_____MODEL_ARCHITECTURE_____#################################################

# cpature some usful dimensions
Tx = features.shape[0]
Ty = labels.shape[0]
height, width, channels = features.shape[1], features.shape[2], features.shape[3]
times_in_dim = times_in.shape[-1]
times_out_dim = times_out.shape[-1]
n_s = 128


#one-step temporal Atttention
class attention(tf.keras.layers.Layer):

	def __init__(self, hidden_units, **kwargs):
		super(attention, self).__init__(hidden_units)
		self.hidden_units = hidden_units
		super(attention, self).__init__(**kwargs)

	def build(self, input_shape):

		self.conv1d_1 = Conv1D(self.hidden_units, kernel_size=1, strides=1, padding='same', activation='relu')
		self.conv1d_2 = Conv1D(self.hidden_units, kernel_size=1, strides=1, padding='same', activation='relu')
		self.conv1d_3 = Conv1D(1, kernel_size=1, strides=1, padding='same', activation='sigmoid')

		self.tanh = tf.keras.layers.Activation("tanh")
		self.alphas = Softmax(axis = 1, name='attention_weights')
		
		super(attention, self).build(input_shape)

	def call(self, enc_output, h_state, c_state):

		h_state_time = K.expand_dims(h_state, axis=1)
		c_state_time = K.expand_dims(c_state, axis=1)
		hc_state_time = concatenate([h_state_time, c_state_time], axis=-1)

		x1 = self.conv1d_1(enc_output)
		x2 = self.conv1d_2(hc_state_time)
		x3 = self.tanh(x1 + x2)
		x4 = self.conv1d_3(x3)
		attn_w = self.alphas(x4) 

		context = attn_w * enc_output
		context = tf.reduce_sum(context, axis=1)
		context = K.expand_dims(context, axis=1)

		return [attn_w, context]

	def compute_output_shape(self):
		return [(input_shape[0], Tx, 1), (input_shape[0], 1, n_s)]

	def get_config(self):
		config = super(attention, self).get_config()
		config.update({"hidden_units": self.hidden_units})
		return config


# instantiate attention layers
temporal_attn = attention(n_s, name="temporal_attention")
spatial_attn = attention(n_s, name="spatial_attention")




def cnn_encoder(ccn_input):
    # input shape -> (batch, time, width, height, features)
    # output shape -> (batch, time, width x height, embedding_size)

	ccn_enc_output = TimeDistributed(Conv2D(16, kernel_size=3, strides=1, activation="relu"))(ccn_input)
	ccn_enc_output = TimeDistributed(AveragePooling2D(pool_size=(2, 2), data_format="channels_last"))(ccn_enc_output)
	# ccn_enc_output = BatchNormalization()(ccn_enc_output)    
	ccn_enc_output = TimeDistributed(Conv2D(32, kernel_size=3, strides=1, activation="relu"))(ccn_enc_output)
	ccn_enc_output = TimeDistributed(Conv2D(64, kernel_size=3, strides=1, activation="relu"))(ccn_enc_output)
	# ccn_enc_output = BatchNormalization()(ccn_enc_output)  
	ccn_enc_output = TimeDistributed(Conv2D(128, kernel_size=3, strides=1, activation="relu"))(ccn_enc_output)
	print(ccn_enc_output.shape)

	ccn_enc_output = Reshape((ccn_enc_output.shape[1], -1, ccn_enc_output.shape[-1]))(ccn_enc_output) 
	# print(ccn_enc_output.shape)

	ccn_enc_output = K.mean(ccn_enc_output, axis=1) 
    
	return ccn_enc_output


def encoder(input, times_in):

	enc_output = K.mean(input, axis=(2,3))

	# concat input time features with input
	enc_output = concatenate([enc_output, times_in], axis=-1)

	enc_output, enc_h, enc_s = lstm_encoder(enc_output)

	return enc_output, enc_h, enc_s



# encoder / decoder layers
encoder_lstm = LSTM(n_s, return_sequences=True, return_state = True)
decoder_lstm = LSTM(n_s, return_sequences=True ,return_state = True)


# layer for output predictions
predict_1 = Conv1D(64, kernel_size=1, strides=1, padding="same", activation="relu")
predict_2 = Conv1D(16, kernel_size=1, strides=1, padding="same", activation="relu")
predict_3 = Conv1D(1, kernel_size=1, strides=1, padding="same", activation="linear")


# define inputs
x_input = Input(shape=(Tx, height, width, channels))
times_in = Input(shape=(Tx, times_in_dim))
times_out = Input(shape=(1, times_out_dim))
y_prev = Input(shape=(1, 1))


# call CCN_encoder function
ccn_enc_output = cnn_encoder(x_input)

# reduce x for lstm input
enc_spatial_inp = K.mean(x_input, axis=(2,3))

# concat input time features with lstm encoder input
enc_spatial_inp = concatenate([enc_spatial_inp, times_in], axis=-1)

# call LSTM_encoder function
lstm_enc_output, state_h, state_c = encoder_lstm(enc_spatial_inp)

# save encoder states 
encoder_states = [state_h, state_c]

# get context matrix (temporal)
attn_weights_temp, context_temp = temporal_attn(lstm_enc_output, state_h, state_c)

# get context matrix (spatial)
attn_weights_spat, context_spat = spatial_attn(ccn_enc_output, state_h, state_c)

# combine spatial and temporal context
context = concatenate([context_spat, context_temp], axis=-1) 

# add known output times
# context = tf.keras.backend.squeeze(context, axis=1)
# context = RepeatVector(Ty)(context)
decoder_input = concatenate([context, times_out], axis=-1)

# get the previous value for teacher forcing
decoder_input = concatenate([decoder_input, y_prev], axis=-1)

# call decoder
dec_output, _, _ = decoder_lstm(decoder_input, initial_state=encoder_states)

# get final predicted value
output = predict_1(dec_output)	
output = predict_2(output)
output = predict_3(output)


	# y_prev = Reshape((1, 1))(y_prev) 
	# y_prev = output
	# y_prev = drop(y_prev)   
	# y_prev = Reshape((1, 1))(y_prev) 
	# print(f'y_prev: {y_prev.shape}')

	# y_prev = tf.identity(output)
	# y_prev = Reshape((1, 1))(y_prev) 

	# append output data
	# all_predictions.append(output)
	# all_temp_attn_weights.append(attn_weights_temp)
	# all_spat_attn_weights.append(attn_weights_spat)


# all_predictions = tf.concat([i for i in all_predictions], axis=0)
# all_temp_attn_weights = tf.concat([i for i in all_temp_attn_weights], axis=0)
# all_spat_attn_weights = tf.concat([i for i in all_spat_attn_weights], axis=0)



# predictions = Lambda(lambda x: concatenate(x, axis=1))(all_predictions)
# attention_temporal = Lambda(lambda x: concatenate(x, axis=1))(all_temp_attn_weights)
# attention_spatial = Lambda(lambda x: concatenate(x, axis=1))(all_spat_attn_weights)

model = Model(inputs = [x_input, times_in, times_out, y_prev], outputs = [output, attn_weights_temp, attn_weights_spat])


# define the pinball loss function to optimise
def defined_loss(q,y,f):
	e = (y - f)
	return K.mean(K.maximum(q*e, (q-1) * e), axis = -1)


# declare quantiles
quantiles = ['0.' + str(i) for i in range(1,10)]
quantiles = list(map(float, quantiles))
quantiles.append(0.99)
quantiles.insert(0, 0.01)
quantiles = [0.5, 0.9]
print(quantiles)

#include clipvalue in optmisier
optimizer = tensorflow.keras.optimizers.Adam(learning_rate = 0.001)

# lstm_idx = [x for x in range(1,49)]

# function to set only decoder to trainable
def freeze_decoder_train(model):
    for layer in model.layers:
        # print(f'*****************************: {layer.name[:4]}')
        if (layer.name[:5] == 'lstm_') or (layer.name == 'conv1d'):
            print('ACTIVATED')
            layer.trainable = True 
        else:
            layer.trainable = False 
    return model


# os.mkdir('/content/drive/My Drive/solar_models')



# for q in quantiles:
# 	# make unique folder for each folder
# 	os.mkdir(f'/content/drive/My Drive/quantile_{q}')
# 	# check if central estimate model exists
# 	if os.path.isfile('/content/drive/My Drive/quantile_0.5/solarGeneration_forecast_MainModel_Q_0.5.h5'):
# 		print('0.5 model present')   
# 		model = load_model('/content/drive/My Drive/quantile_0.5/solarGeneration_forecast_MainModel_Q_0.5.h5', custom_objects = {'<lambda>': lambda y,f: defined_loss(q,y,f), 'attention': attention})
# 		# re-compile model with new loss for current quantile 
# 		model.compile(loss = [lambda y,f: defined_loss(q,y,f), None, None], optimizer= optimizer, metrics = ['mae'])
# 		# load trained weights from q_0.5
# 		model.load_weights(f'/content/drive/My Drive/quantile_0.5/solarGeneration_forecast_weights_Q_0.5.h5')
# 		# freeze all weights apart from decoder fro re-train
# 		model = freeze_decoder_train(model)
# 		print(model.summary())
# 		model.fit(training_generator, epochs = 10)
# 		enc_model_temp_test.save(f'/content/drive/My Drive/quantile_{q}/solarGeneration_encoderModelTemporal_Q_{q}.h5')
# 		enc_model_spat_test.save(f'/content/drive/My Drive//quantile_{q}/solarGeneration_encoderModelSpatial_Q_{q}.h5')
# 		# model.save(f'/content/drive/My Drive/quantile_{q}/solarGeneration_forecast_MainModel_Q_{q}.h5')
# 	else:
# 		print('New Model') 
# 		# train median model for reference to other qunatiles
# 		model.compile(loss = [lambda y,f: defined_loss(q,y,f), None, None], optimizer= optimizer, metrics = ['mae'])
# 		print(model.summary())
# 		# sys.exit()
# 		model.fit(training_generator, epochs = 10)
# 		# save wegihts 
# 		model.save_weights(f'/content/drive/My Drive/quantile_{q}/solarGeneration_forecast_weights_Q_{q}.h5')
# 		# save some additional models for inference
# 		enc_model_temp_test = Model(inputs = [x_input, times_in], outputs=[lstm_enc_output])
# 		enc_model_spat_test = Model(x_input, ccn_enc_output)
# 		enc_model_temp_test.save(f'/content/drive/My Drive/quantile_{q}/solarGeneration_encoderModelTemporal_Q_{q}.h5')
# 		enc_model_spat_test.save(f'/content/drive/My Drive//quantile_{q}/solarGeneration_encoderModelSpatial_Q_{q}.h5')
# 		# model.save(f'/content/drive/My Drive/quantile_{q}/solarGeneration_forecast_MainModel_Q_{q}.h5')

# 	model.save(f'/content/drive/My Drive/quantile_{q}/solarGeneration_forecast_MainModel_Q_{q}.h5')	
# 	K.clear_session()


# dec_state_input_h = Input(shape=(n_s,))
# dec_state_input_c = Input(shape=(n_s,))
# dec_states_inputs = [dec_state_input_h, dec_state_input_c]
# dec_output, state_h, state_c = decoder_lstm(decoder_input, initial_state=dec_states_inputs)
# decoder_states = [state_h, state_c]
# decoder_model = Model([decoder_input] + dec_states_inputs, [output] + decoder_states)





# train each model for each quantile
for q in quantiles:
	print(q)
	# model = solarGenation_Model()
	model.compile(loss = [lambda y,f: defined_loss(q,y,f), None, None], optimizer= optimizer, metrics = ['mae'])
	print(model.summary())
	train = model.fit(training_generator, workers=1, epochs = 1, shuffle=True)

	os.mkdir(f'/content/drive/My Drive/solarModels/q_{q}')
	# model_freeze.save_weights('/content/drive/My Drive/solarGeneration_forecast_weights_freezed' + '_Q_%s' %(q) + '.h5')
	model.save(f'/content/drive/My Drive/solarModels/q_{q}/solarGeneration_forecast_MainModel' + '_Q_%s' %(q) + '.h5')
	# model.save_weights('/content/drive/My Drive/solarGeneration_forecast_weights_test2' + '_Q_%s' %(q) + '.h5')
	
	# save some additional models for inference
	enoder_temporal_model = Model(inputs = [x_input, times_in], outputs=[lstm_enc_output, encoder_states])
	enoder_spatial_model = Model(x_input, ccn_enc_output)

	enoder_temporal_model.save(f'/content/drive/My Drive/solarModels/q_{q}/solarGeneration_encoderModelTemporal' + '_Q_%s' %(q) + '.h5')
	enoder_spatial_model.save(f'/content/drive/My Drive/solarModels/q_{q}/solarGeneration_encoderModelSpatial' + '_Q_%s' %(q) + '.h5')
	model.save(f'/content/drive/My Drive/solarModels/q_{q}/solarGeneration_main' + '_Q_%s' %(q) + '.h5')

	K.clear_session()

sys.exit()

# empty dictionaries for decoder models
decoder_models, enoder_temporal_models, enoder_spatial_models = {}, {}, {}





######## model for inference #############
def inference_model(idx):

	# LSTM Encoder
	enc_model_temp_test = Model(inputs = [x_input, times_in], outputs=[lstm_enc_output])
	# CNN Encoder
	enc_model_spat_test = Model(x_input, ccn_enc_output)

	# Encoder outputs for setup
	ccn_enc_output_test = Input(shape=(320, 256))
	lstm_enc_output_test = Input(shape=(Tx, n_s + times_in_dim))

	# Decoder Input
	dec_input_test = Input(shape=(1, 1))
	dec_input_test_int = Input(shape=(1, n_s + times_in_dim))
	times_out_test = Input(shape=(1, times_out_dim))

	# context and previous output
	attn_weights_temp_test, context_temp_test = model.get_layer('temporal_attention')(lstm_enc_output_test, s_state0, c_state0)
	attn_weights_spat_test, context_spat_test = model.get_layer('spatial_attention')(ccn_enc_output_test, s_state0, c_state0)

	# context & previous output combine
	context_test = concatenate([context_spat_test, context_temp_test], axis=-1) 
	dec_input_concat_test = concatenate([context_test, dec_input_test], axis=-1)
	dec_input_concat_test_int = concatenate([context_test, dec_input_test_int], axis=-1)

	# combine with decoder inputs
	dec_input_concat_test = concatenate([dec_input_concat_test, times_out_test], axis=-1)
	dec_input_concat_test_int = concatenate([dec_input_concat_test_int, times_out_test], axis=-1)

	# Decoder inference
	dec_output, s_state, c_state = model.get_layer('lstm_1')(dec_input_concat_test, initial_state=[s_state0, c_state0])
	# if idx == 1:
	# 	dec_output, s_state, c_state = model.get_layer('lstm_1')(dec_input_concat_test_int, initial_state=[s_state0, c_state0])
	# else:   
	# 	dec_output, s_state, c_state = model.get_layer(f'lstm_{idx}')(dec_input_concat_test, initial_state=[s_state0, c_state0])

	pred_test = predict_1(dec_output)
	pred_test = predict_2(pred_test)

	# Inference Model
	deoceder_test_model = Model(inputs=[dec_input_test, dec_input_test_int, times_out_test, lstm_enc_output_test, ccn_enc_output_test, s_state0, c_state0], outputs=[pred_test, s_state, c_state, attn_weights_temp_test, attn_weights_spat_test])  
	     
	return deoceder_test_model


# for idx in range(1, Ty+1):
# 	enoder_temporal_model, enoder_spatial_model, decoder_models[f'{idx}'] = inference_model(idx)
decoder_inference = inference_model(1)
# print(decoder_models)
# print(decoder_models[f'{idx}'][0])
# sys.exit()

print('decoder loaded')
############_________Inference__________##############
sample_size = 200
# main_input = train_set['X1_train'][:sample_size,:,:,:,:]
# times_in = train_set['X2_train'][:sample_size,:,:]
# times_out = train_set['X3_train'][:sample_size,:,:]
# y_train = train_set['y_train'][:sample_size,:,:]
s0 = np.zeros((sample_size, n_s))
c0 = np.zeros((sample_size, n_s))

s_state = s0
c_state = c0
predictions = []

# inference run
enc_temp_out = enoder_temporal_model.predict([train_set['X1_train'][:sample_size,:,:,:,:], train_set['X2_train'][:sample_size,:,:]])
enc_spat_out = enoder_spatial_model.predict(train_set['X1_train'][:sample_size,:,:,:,:])

print('encoder models ran')

# intial decoder input
dec_input_int = enc_temp_out[:,-1,:]
dec_input_int = K.expand_dims(dec_input_int, axis=1)
# dec_input = np.zeros((sample_size, 1, 1))

dec_input = enc_temp_out[:,-1,-1]
dec_input = K.expand_dims(dec_input, axis=1)
dec_input = K.expand_dims(dec_input, axis=-1)

for t in range(1, Ty+1):

	print(t)

	# get current 'times out' reference
	times_out_single = times_out[:,t-1,:]
	times_out_single = K.expand_dims(times_out_single, axis=1)

	# print(dec_input.shape)
	# print(times_out_single.shape)
	# print(enc_temp_out.shape)
	# print(enc_spat_out.shape)
	# print(s_state.shape)
	# print(c_state.shape)

    # dec_output, s_state, c_state = decoder(decoder_input, times_out_single, s_state, c_state)
	prediction, s_state, c_state, temporal_attention, spatial_attention = decoder_inference.predict([dec_input, dec_input_int, times_out_single, enc_temp_out, enc_spat_out, s_state, c_state])

	# dec_input = y_train[:,t-1,:]
	dec_input = prediction
	# print('dec_input')
	# print(dec_input.shape)

	# predictions.append(prediction)
    
	if t == 1:
		predictions_test = prediction
		total_temporal_attn_test = temporal_attention
		total_spatial_attn_test = spatial_attention
	else:
		predictions_test = np.concatenate([predictions_test, prediction], axis=1)
		total_temporal_attn_test = np.concatenate([total_temporal_attn_test, temporal_attention], axis=-1)
		total_spatial_attn_test = np.concatenate([total_spatial_attn_test, spatial_attention], axis=-1)
	

	print(total_temporal_attn_test.shape)
	print(total_spatial_attn_test.shape)


#function for plotting temporal attention
def temporal_attention_graph(x, y, y_hat, att_w_temp):

	fig = plt.figure(figsize=(24, 8))
	gs = gridspec.GridSpec(ncols=90, nrows=100)

	upper_axis = fig.add_subplot(gs[0:20, 10:75])
	left_axis = fig.add_subplot(gs[25:, 0:8])
	atten_axis = fig.add_subplot(gs[25:, 10:])

	upper_axis.plot(x)
	upper_axis.set_xlim([0, Tx])
	upper_axis.set_ylim([0, 0.5])
	upper_axis.set_xticks(range(0, Tx))
	upper_axis.set_xticklabels(range(0, Tx))

	left_axis.plot(y, range(0,Ty), label='True')
	left_axis.plot(y_hat, range(0,Ty), label='Prediction')
	left_axis.set_ylim([0, Ty])
	left_axis.set_yticks(range(0, Ty, 4))
	left_axis.set_yticklabels(range(0, Ty, 4))
	left_axis.invert_yaxis()
	left_axis.legend()
    

	sns.heatmap(att_w_temp, cmap='flare', ax = atten_axis)
	atten_axis.set_xticks(range(0, Tx))
	atten_axis.set_xticklabels(range(0, Tx))
	atten_axis.set_yticks(range(0, Ty, 4))
	atten_axis.set_yticklabels(range(0, Ty, 4))

	plt.show()



# input1 = train_set['X1_train'][:sample_size,:,:,:,:]
# input2 = train_set['X2_train'][:sample_size,:,:]
# input3 = train_set['X3_train'][:sample_size,:,:]
# outputs = train_set['y_train'][:sample_size,:,:]

# n_s = 128

s0 = np.zeros((sample_size, n_s))
c0 = np.zeros((sample_size, n_s))


# performance against training data
inputs = [train_set['X1_train'][:sample_size,:,:,:,:], train_set['X2_train'][:sample_size,:,:], train_set['X3_train'][:sample_size,:,:], s0, c0, train_set['y_train'][:sample_size,:,:]]

print('predicitng...')
yhat1 = model.predict(inputs)
model_out1 = yhat1[0]
attentions_temp_train = yhat1[1]


idx = 884
x = np.average(train_set['X1_train'], axis=(2,3))[idx, :]
y = outputs[idx, :, 0]
y_hat_train = model_out1[idx]
y_hat_test = predictions_test[idx]

print('prediction_test_Size')
print(predictions_test.shape)


print(x.shape)
print(y.shape)
print(y_hat_train.shape)
print(y_hat_test.shape)



# train temporal attention
att_w_temp_train = np.transpose(attentions_temp_train[idx])
# test temporal attention
att_w_temp_test = np.transpose(total_temporal_attn_test[idx])


temporal_attention_graph(x, y, y_hat_train, att_w_temp_train)

temporal_attention_graph(x, y, y_hat_test, att_w_temp_test)




















