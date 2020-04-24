#! /usr/bin/python3

import sys
import os
import errno
import traceback

from eml2token import eml2str,tokenize,eprint

from ds_model import deepspam_load,deepspam_test

wordmap=deepspam_load()



def do_eml(eml):
    vtokens=[]
    tokens=[]
    for text in eml2str(eml):
      if text.find('pam detection software, running on the system')>=0:
        continue
      t=" ".join(text.replace('"',' ').split())
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
    print("NUM of tokens: %d / %d"%(len(vtokens),len(tokens)))
    if len(vtokens)<10:
        return "toosmall"

    print(" ".join(vtokens))
    res=deepspam_test(vtokens)
    res+=0.1
    print(res)
    try:
        f=open("test_res","at")
        f.write("%3d%%:"%(res)+" ".join(tokens)+"\n")
        f.close()
    except:
        pass
    if res<=10:
        return "ham-%d"%(res)
    if res<20:
        return "ham-maybe"
    if res>=90:
        return "spam-%d"%(res)
    if res>80:
        return "spam-maybe"
    return "dunno"


########################################################################################################################################


input_stream= open("test.input","rb")

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
            print("Parsing email (%d bytes)"%(len(eml)))
            res=do_eml(eml)
#            print(res)
#            out_mbox = open("test_"+res,"at",encoding="utf-8",errors='ignore')
            out_mbox = open("test_"+res,"ab")
            out_mbox.write(eml)
            out_mbox.close()
            eml=None
        in_hdr=1
    if eml:
        eml+=line
    else:
        eml=line
#if eml:
#    do_eml(eml)

deepspam_exit()
