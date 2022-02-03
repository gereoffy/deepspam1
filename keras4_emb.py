#! /usr/bin/python3

import os
import sys
import pickle
import json

#os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# np.random.seed(1080)

import numpy as np

#from keras.preprocessing.text import Tokenizer
#from keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.layers import (
    Dense, Input, GlobalMaxPooling1D,
    Conv1D, MaxPool1D, MaxPooling1D, Embedding,
    Dropout, Flatten, Convolution1D, BatchNormalization, Concatenate, Activation,
    Bidirectional, LSTM #, CuDNNLSTM, CuDNNGRU
)
#from tensorflow.keras.layers.recurrent import LSTM
from tensorflow.keras.models import Model
#from tensorflow.keras.utils import plot_model



WORDVEC_DIR = ''
TEXT_DATA_DIR = 'data'

MAX_SEQUENCE_LENGTH = 100

print('Loading embedding_matrix')
wordmap,embedding_matrix = pickle.load(open("all12sg.pck32.1M", "rb"))
#wordmap,embedding_matrix = pickle.load(open("all8sg.pck32.1M", "rb"))

num_words=len(embedding_matrix)
num_dim=len(embedding_matrix[0])
print('%d words found, dim=%d'%(num_words,num_dim))

print('Processing text dataset')
texts = []  # list of text samples
labels_index = ["spam","ham"]  # dictionary mapping label name to numeric id
labels = []  # list of label ids

def loadtext(path,label_id):
    for t in open(TEXT_DATA_DIR+"/"+path,"r"):
        texts.append(t)
        labels.append(label_id)

loadtext("mail.neg",0)
loadtext("mail.pos",1)
num_train=len(texts)
loadtext("mail.negT",0)
loadtext("mail.posT",1)
num_all=len(texts)
num_val=num_all-num_train
print('Found %d texts. (%d+%d)' % (num_all,num_train,num_val))

data = np.zeros((num_all, MAX_SEQUENCE_LENGTH), dtype='int32')
wcount_all=0
wcount_ok=0
for i in range(num_all):
    j=0
    for w in texts[i].strip().split(" "):
        wcount_all+=1
        if w in wordmap:
            wcount_ok+=1
            if j<MAX_SEQUENCE_LENGTH:
                data[i][j]=wordmap[w]
                j+=1
print('%d tokens found (%d has embeddings)'%(wcount_all,wcount_ok))

print('Shape of data tensor:', data.shape)
#Shape of data tensor: (118952, 100)

labels = to_categorical(np.asarray(labels))
print('Shape of label tensor:', labels.shape)
#Shape of label tensor: (118952, 2)


# split the data into a training set and a validation set
indices = np.arange(num_train)
np.random.shuffle(indices)
x_train = data[indices]
y_train = labels[indices]
print('Shape of TRAIN:', x_train.shape, y_train.shape)

x_val = data[-num_val:]
y_val = labels[-num_val:]
t_val = texts[-num_val:]
print('Shape of TEST:', x_val.shape, y_val.shape)





#print("Loading dataset... (alldata2.pck)")
#alldata = pickle.load(open("alldata2.pck", "rb"))
#x_train,y_train,x_val,y_val,t_val,num_words,embedding_matrix,labels_index=alldata
print('!!! Shape of x/y:', x_train.shape, y_train.shape)


# note that we set trainable = False so as to keep the embeddings fixed
embedding_layer = Embedding(num_words,
                            num_dim,
                            weights=[embedding_matrix],
                            trainable=False)

model_input = Input(shape=x_train[0].shape, dtype='int32')
emb_input = embedding_layer(model_input)
print('!!! Shape of embedded input:', emb_input.shape)
z = Dropout(0.2)(emb_input)
#z = Dropout(0.5)(emb_input)
# Convolutional block
conv_blocks = []

# LTSM:
#zl=CuDNNLSTM(128)(emb_input)
#zl=LSTM(256, dropout=0.2, recurrent_dropout=0.2)(emb_input)
#conv_blocks.append(zl)

#filter_sizes = (2,3,4,5,7,9,11,15)
filter_sizes = [2,3,4,5]
for sz in filter_sizes:
    conv = Convolution1D(filters=128,
                         kernel_size=sz,
                         padding="valid",
                         activation="relu",
                         strides=1)(z)
#    conv = MaxPooling1D(pool_size=MAX_SEQUENCE_LENGTH+1-sz)(conv)
#    conv = Flatten()(conv)
    conv = GlobalMaxPooling1D()(conv)
    conv_blocks.append(conv)
z = Concatenate()(conv_blocks)

z = Dropout(0.5)(z)

z = Dense(32, activation="relu")(z)

#z = Activation("relu")(z)
#z = BatchNormalization()(z)

#z = Dropout(0.75)(z)
#z = Dropout(0.5)(z)

model_output = Dense(len(labels_index), activation="sigmoid")(z)
#model_output = Dense(len(labels_index), activation="softmax")(z)

model = Model(model_input, model_output)
#model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])
model.compile(loss='categorical_crossentropy', optimizer='adam',metrics = ['accuracy'])

print(model.summary())
#plot_model(model, to_file='model.png', show_shapes=True)

model.fit(x_train, y_train,
          batch_size=256,
          epochs=100,
          validation_data=(x_val, y_val))


print("Save:")

#json.dump(model.get_config(),open("model.config","wt"),sort_keys=False,indent=4)
model.save("model/")

json.dump(model.get_config(),open("model/config.json","wt"),sort_keys=False,indent=4)

#model.save_weights("model.weights2",save_format="tf")

#model.save("model.h5")
#model.save_weights("model.weights")
#model.save_weights("model.weights.h5")
#model.save_weights("model.weights1",save_format="h5")

#pickle.dump(model.get_weights(), open("model.weights.pck", "wb"))
#pickle.dump(wordmap, open("model.wordmap-py2", "wb"), 2)
pickle.dump(wordmap, open("model/model.wordmap", "wb"))

#print(model.get_config())
#pickle.dump(model.get_config(), open("model.c", "wb"))
#pickle.dump(model.get_weights(), open("model.w", "wb"))


#w=model.get_weights()
#for k in w:
#    print("WEIGHT",len(k))
#    print(k)

print("Evaluate:")
loss_and_metrics = model.evaluate(x_val, y_val, batch_size=128)
print(loss_and_metrics)

classes = model.predict(x_val, batch_size=128, verbose=1)
f=open("test.res","wt")
for i in range(len(classes)):
    f.write("%3d %%  [%d/%d]   %8.5f / %8.5f  %s"%(classes[i][0]*100.0/(classes[i][0]+classes[i][1]) ,  y_val[i][0],y_val[i][1],classes[i][0],classes[i][1],t_val[i]))
#    print("%5d.:  %3d%%  [%d/%d]   %8.5f / %8.5f"%(i, classes[i][0]*100.0/(classes[i][0]+classes[i][1]) ,  y_val[i][0],y_val[i][1],classes[i][0],classes[i][1]))
f.close()

#print(model.to_json())


