###
### DeepSpam neural model loader
###
### Ebben a verzioban a keras/tensorflow tobb threadbol is hivhato ugyanazzal a modellel, hogy ez mukodjon, a model read onlyra van allitva (finalize), es fixalva van a session is
### Ez kell az ujabb, atmeneti keras+tensorflow verziohoz, ami mar belul multithreaded.
### Viszont ez a regebbi keras-al nem mukodik (random befagy), pl. amit Ubuntu 18.04-ben apt-vel raksz fel. A pip3-al felrakott verzioval jo.
###

import sys
import os
import errno
import traceback

import pickle
import json

# force CPU:
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# np.random.seed(1080)

import numpy as np
#from keras.preprocessing.text import Tokenizer
#from keras.preprocessing.sequence import pad_sequences
#from keras.utils import to_categorical
import tensorflow
from tensorflow.keras.layers import (
    Dense, Input, GlobalMaxPooling1D,
    Conv1D, MaxPool1D, MaxPooling1D, Embedding,
    Dropout, Flatten, Convolution1D, BatchNormalization, Concatenate, Activation
)
from tensorflow.keras.models import Model
from tensorflow.keras import backend as K

MAX_SEQUENCE_LENGTH = 100

def deepspam_load(path="model"):
    global wordmap
    global model

#    global tf_session
#    print('Creating TF session...')
#    config = tensorflow.ConfigProto(
#                intra_op_parallelism_threads=1,
#                allow_soft_placement=True
#            )
#    tf_session = tensorflow.Session(config=config)
#    tensorflow.set_session(tf_session)

    global tf_session
    global tf_graph

    print('Loading Model...')
    config=json.load(open(path+"/model.config","rt"))
    model = Model.from_config(config)
    model.load_weights(path+"/model.weights")
####weights=pickle.load(open("model.weights", "rb"))
#model.set_weights(weights)
    try:
        wordmap=pickle.load(open(path+"/model.wordmap-py3", "rb"))
    except:
        wordmap=pickle.load(open(path+"/model.wordmap-py2", "rb"))
#wordmap=[]
    print("MODEL loaded! (%d words)"%(len(wordmap)))

    # testing
    data = np.zeros((1, MAX_SEQUENCE_LENGTH), dtype='int32')
    classes = model.predict(data, batch_size=1, verbose=1)

    tf_session=K.get_session()
    tf_graph = tensorflow.get_default_graph() 
    tf_graph.finalize()
    print("MODEL finalized!")

    return wordmap

def deepspam_exit():
    pass


def deepspam_test(vtokens):
#    print(" ".join(vtokens))
    data = np.zeros((1, MAX_SEQUENCE_LENGTH), dtype='int32')
    j=0
    for w in vtokens:
        if w in wordmap:
            data[0][j]=wordmap[w]
            j+=1
        if j>=MAX_SEQUENCE_LENGTH:
            break

#    print("Predict:")
    with tf_session.as_default():
        with tf_graph.as_default():
            classes = model.predict(data, batch_size=1, verbose=1)
    res=classes[0][0]*100.0/(classes[0][0]+classes[0][1])
#    res+=0.1
#    print(res)
    return res

