###
### DeepSpam neural model loader
###
### Ez a regi, nem multithreaded verzio.
### Mivel az ujabb tensorflow-ba mar beolvasztottak a keras-t, eloszor azt probalja betolteni, ha nem megy, akkor a kulon modult.
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

try:
    from tensorflow.keras.models import load_model
    from tensorflow.keras.models import Model
except:
    from keras.models import load_model
    from keras.models import Model


MAX_SEQUENCE_LENGTH = 100

def deepspam_load(path="model"):
    global wordmap
    global model
    print('Loading Model...')
    try:
        # new tf2 format:
        model=load_model(path)
        wordmap=pickle.load(open(path+"/model.wordmap", "rb"))
    except:
        # old json+h5 format:
        config=json.load(open(path+"/model.config","rt"))
        model = Model.from_config(config)
        model.load_weights(path+"/model.weights")
        try:
            wordmap=pickle.load(open(path+"/model.wordmap-py3", "rb"))
        except:
            wordmap=pickle.load(open(path+"/model.wordmap-py2", "rb"))
#wordmap=[]
    print("MODEL loaded! (%d words)"%(len(wordmap)))
    return wordmap

def deepspam_exit():
    pass


def deepspam_test(vtokens,verbose=1):
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
    classes = model.predict(data, batch_size=1, verbose=verbose)
    res=classes[0][0]*100.0/(classes[0][0]+classes[0][1])
    if res>=0 and res<=100: return res
    print("Predict: %f - %f"%(classes[0][0],classes[0][1]))
    return 50.0
#    res+=0.1
#    print(res)
#    return res

