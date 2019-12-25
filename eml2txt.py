#! /usr/bin/python3

import io
import os
import sys
import pickle
import traceback

from eml2token import eml2str,tokenize,eprint,html_unescape

#wordmap=pickle.load(open("model/model.wordmap", "rb"))



def do_eml(eml,out_txt):
#    print("Parsing email (%d bytes)"%(len(eml)))
    vtokens=[]
    tokens=[]
    for text in eml2str(eml):
#      print(text.encode("utf-8"))
      if text.find('pam detection software, running on the system')>=0:
        continue
      for t in ["-----","_____",".....","From:","Forwarded","Felad"]:
        p=text.find(t)
        if p>=0:
          text=text[0:p]
      if len(text)>100:
        try:
          tok=html_unescape(text).replace('"',' ').split()
#      print(t.encode("utf-8"))
#        print(str(label)+" "+t.encode("utf-8"))
#        print(t.encode("utf-8"))
#          vtok,tok=tokenize(t,wordmap)
          vtok=[]
          for t in tok:
            if len(t)>=3 and t[0]>='A':
              vtok.append(t)
          if len(vtok)>len(vtokens):
            vtokens=vtok
            tokens=tok
        except:
          eprint(traceback.format_exc())
#    eprint("NUM of tokens: %d / %d"%(len(vtokens),len(tokens)))
#    eprint("%d / %d"%(bestnn,len(tokens)))
    if len(vtokens)<20 or len(tokens)<30:
        return 0
    out_txt.write(" ".join(tokens)+"\n")
    return 1

#    ok=dedup(vtokens,5,(len(vtokens)-10)/3)
#    ok=dedup(vtokens,7,(len(vtokens)-10)*4/5)
#    print(ok)
#    if ok:
#        print(" ".join(tokens)+"\n")
#        out_txt.write(" ".join(tokens)+"\n")

#    return ok



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
#output_stream= open("maildedup.mbox","wb")
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
#            if res:
#                output_stream.write(eml)
            eml=None
        in_hdr=1
    if eml:
        eml+=line
    else:
        eml=line
if eml:
    res=do_eml(eml,output_txt)
#    if res:
#        output_stream.write(eml)

#output_stream.close()
output_txt.close()
