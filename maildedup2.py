#! /usr/bin/python3

import io
import os
import sys
import pickle
import traceback

from eml2token import eml2str,tokenize,eprint

try:
    wordmap=pickle.load(open("model/model.wordmap-py3", "rb"))
except:
    wordmap=pickle.load(open("model/model.wordmap-py2", "rb"))

###########################################################################################################
################################################### DEDUP #################################################
###########################################################################################################

wmem=bytearray(2*65536*65536)  # 8GB ram!!!
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

def dedup1(tokens):
        w=" ".join(tokens)
        wh=hash(w)
        wh^=(wh>>40)
        wh&=maxhash
#            print(wh)
#            try:
        if wmem[wh>>3] & (1<<(wh&7)):
            return 0
        wmem[wh>>3]|=(1<<(wh&7))
        return 1


#################################################################################################################################################################



def do_eml(eml,out_txt):
#    print("Parsing email (%d bytes)"%(len(eml)))
    vtokens=[]
    tokens=[]
    for text in eml2str(eml):
#      print(text.encode("utf-8"))
      if text.find('pam detection software, running on the system')>=0:
        continue
      t=" ".join(text.replace('"',' ').split())
#      print(t.encode("utf-8"))
      if(len(t)>10):
#        print(str(label)+" "+t.encode("utf-8"))
#        print(t.encode("utf-8"))
        try:
          vtok,tok=tokenize(t,wordmap)
          if len(vtok)>len(vtokens):
            vtokens=vtok
            tokens=tok
        except:
          eprint(traceback.format_exc())
#    print("NUM of tokens: %d / %d"%(len(vtokens),len(tokens)))
#    print("%d / %d"%(bestnn,len(tokens)))
    if len(vtokens)<10:
        return 0

    ok=dedup(vtokens,5,(len(vtokens)-10)/3)
#    ok=dedup(vtokens,7,(len(vtokens)-10)*4/5)
#    ok=dedup1(vtokens)
#    print(ok)
    if ok:
#        print(" ".join(tokens)+"\n")
        out_txt.write(" ".join(tokens)+"\n")

    return ok



########## MAIN ##############

#for line in open("vocab.txt"):
#    w,c=line.strip().split(" ")
#    vocab[w]=int(c)

#input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='iso-8859-2',errors='ignore')
#input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8',errors='ignore')
#output_stream= open("maildedup.mbox","wt",encoding="utf-8",errors='ignore'):
#input_stream = sys.stdin
#output_stream = sys.stdout
#output_txt = open("maildedup.txt","wt",encoding="utf-8",errors='ignore')
input_stream= open(sys.argv[1],"rb")
output_stream= open("maildedup.mbox","wb")
output_txt = open("maildedup.txt","w")

in_hdr=0
eml=None
for line in input_stream:
    if in_hdr:
#	eml+=line
        if len(line.rstrip())==0:
            in_hdr=0
    elif line[0:5]==b'From ':
#        print(line)
        if eml:
            res=do_eml(eml,output_txt)
            if res:
                output_stream.write(eml)
            eml=None
        in_hdr=1
    if eml:
        eml+=line
    else:
        eml=line
if eml:
    res=do_eml(eml,output_txt)
    if res:
        output_stream.write(eml)

output_stream.close()
output_txt.close()
