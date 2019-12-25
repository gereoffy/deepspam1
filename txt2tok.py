#! /usr/bin/python3

import sys
import os
import errno
import traceback
import pickle
import io

from eml2token import eml2str,tokenize,eprint

wordmap=pickle.load(open("model/model.wordmap-py3", "rb"))

###########################################################################################################
################################################### DEDUP #################################################
###########################################################################################################

wmem=bytearray(65536*65536)  # 16GB ram!!!
maxhash=8*len(wmem)-1

# hl=mozgo ablak merete amit hashel.  nn=maximum egyezesek szama
def dedup(tokens,hl,nn):
        # fuzzy search
        ok=0
        n=len(tokens)-(hl-1)
        for i in range(n):
            w=" ".join(tokens[i:i+hl])
            wh=hash(w)
            wh^=(wh>>40)
            wh&=maxhash
#            print(wh)
#            try:
            if wmem[wh>>3] & (1<<(wh&7)):
                ok+=1
                if ok>nn:
                    return 0
#                break
#            except:
#              print(type(wh))
        if ok<=nn:
#        if ok:
#            o=" ".join(tokens)
#            print(o)
            for i in range(n):
                w=" ".join(tokens[i:i+hl])
                #wh=hash(w) & maxhash
                wh=hash(w)
                wh^=(wh>>40)
                wh&=maxhash
                wmem[wh>>3]|=(1<<(wh&7))
            return 1
#        print(o.encode("utf-8"))
#	print str(label)+" "+" ".join(tokens)
        return 0

###########################################################################################################
###########################################################################################################
###########################################################################################################






input_stream=io.open(sys.argv[1],"rt",encoding="utf-8",errors="ignore")
output_stream=io.open(sys.argv[1]+".TOK","wt",encoding="utf-8")

for line in input_stream:
#  t=" ".join(line.replace('"',' ').split())
  vtok,tok=tokenize(line,wordmap)
  if len(vtok)<5 or len(tok)<20:
    continue
  ok=dedup(tok,7,(len(tok)-10)*4/5)
#  print("%4d /%4d   -> %d"%(len(vtok),len(tok),ok))
  if ok:
    output_stream.write(" ".join(tok)+"\n")

output_stream.close()
