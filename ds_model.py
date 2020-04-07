
import sys
import os
import errno
import traceback
import time

import pickle
import json

# force CPU:
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# np.random.seed(1080)

import numpy as np
#from keras.preprocessing.text import Tokenizer
#from keras.preprocessing.sequence import pad_sequences
#from keras.utils import to_categorical
#import tensorflow
#from tensorflow.keras.layers import (
#    Dense, Input, GlobalMaxPooling1D,
#    Conv1D, MaxPool1D, MaxPooling1D, Embedding,
#    Dropout, Flatten, Convolution1D, BatchNormalization, Concatenate, Activation
#)
from tensorflow.keras.models import Model
#from tensorflow.keras import backend as K

import threading
import queue


MAX_SEQUENCE_LENGTH = 100

def dprint(text):
    print(text)




def deepspam_worker(q,path):
    print('Loading Model...')
    config=json.load(open(path+"/model.config","rt"))
    model = Model.from_config(config)
    model.load_weights(path+"/model.weights")
####weights=pickle.load(open("model.weights", "rb"))
#model.set_weights(weights)
#wordmap=[]
#    print("MODEL loaded! (%d words)"%(len(wordmap)))
    print("worker: started!!!")
    while True:
        dprint("worker: waiting for job... (%d)"%(q.qsize()))
        data,retq = q.get()
        if not retq:
            break
        dprint("worker: new job!")
        classes = model.predict(data, batch_size=1, verbose=1)
        res=classes[0][0]*100.0/(classes[0][0]+classes[0][1])
        dprint("worker: result="+str(res))
        retq.put(res)
        q.task_done()
    print("worker: exiting!!!")
    q.task_done()


def deepspam_exit():
    dprint("stop: sending None to worker")
    deepq.put((None,None))
    dprint("stop: waiting for join...")
    deepq.join()
    dprint("stop: done")


def deepspam_load(path="model"):
    global wordmap
    global deepq
#    global model

#    global tf_session
#    print('Creating TF session...')
#    config = tensorflow.ConfigProto(
#                intra_op_parallelism_threads=1,
#                allow_soft_placement=True
#            )
#    tf_session = tensorflow.Session(config=config)
#    tensorflow.set_session(tf_session)

    try:
        wordmap=pickle.load(open(path+"/model.wordmap-py3", "rb"))
    except:
        wordmap=pickle.load(open(path+"/model.wordmap-py2", "rb"))

    deepq = queue.Queue()

    t = threading.Thread(target=deepspam_worker, args=(deepq,path))
    t.start()

#    # testing
#    data = np.zeros((1, MAX_SEQUENCE_LENGTH), dtype='int32')
#    classes = model.predict(data, batch_size=1, verbose=1)
#    global tf_session
#    global tf_graph
#    tf_session=K.get_session()
#    tf_graph = tensorflow.get_default_graph() 
#    tf_graph.finalize()
#    print("MODEL finalized!")

    return wordmap



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

    t0=time.time()
    retq = queue.Queue()
    dprint("test: sending data...")
    deepq.put((data,retq))
    dprint("test: waiting for response...")
    try:
        ret=retq.get(block=True, timeout=15)
        t0=time.time()-t0
        dprint("test: got response: %5.3f   time=%8.6f"%(ret,t0))
        retq.task_done()
    except queue.Empty:
        dprint("test: waiting timeout!")
        ret=0.5
    return ret

