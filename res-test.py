#! /usr/bin/python3

import zstandard
import time
#import lzma

from ds_model import deepspam_load,deepspam_test
wordmap=deepspam_load()

wmem=bytearray(65536*65536)
maxhash=8*len(wmem)-1


f=zstandard.open("deepspam.res.OLD.zst","rt",encoding="utf-8")
#f=lzma.open("deepspam.res.OLD.zst","rt",encoding="utf-8")
#        f.write("%3d%%:"%(res)+" ".join(tokens)+"\n")
lineno=0
total=0
hiba=0
hiba1=0
hiba2=0
t0=time.time()
tt=0
for line in f:
    lineno+=1
    if "sajnalom de rossz hirem van szamodra ! egy par honappal ezelott" in line: continue
    ress,txt=line.strip().split(":",1)

    # dedup
    wh=hash(txt)
    wh^=(wh>>40)
    wh&=maxhash
    if wmem[wh>>3] & (1<<(wh&7)): continue
    wmem[wh>>3]|=(1<<(wh&7))

    res=int(ress.replace("%",""))
    tokens=txt.split(" ")
    t1=time.time()
    res2=int(deepspam_test(tokens,verbose=0)+0.1)
    t1=time.time()-t1
    tt+=t1
    dif=res-res2
    total+=1
    p=" "
    if res<=20 and res2>=80:
        hiba1+=1
        p="+"
    elif res2<=20 and res>=80:
        hiba2+=1
        p="-"
    elif res<2 and res2>=2:
        p="?"
    elif res2<2 and res>=2:
        p="!"
    elif res>=98 and res2<98:
        p="?"
    elif res2>=98 and res<98:
        p="!"
    if dif<0: dif=-dif
    if dif: hiba+=1
    if dif>20:
        print("%3d -> %3d  %s %3d  %3d%%  %3d%% %d/%d   %s"%(res,res2,p,dif, 100*hiba/total, 100*(hiba1+hiba2)/total, hiba1,hiba2, (" ".join(tokens))[:120] ))
    t2=time.time()-t0
    print("%d/%d    tt=%d/%d    %d/%d lines/sec\r"%(total,lineno, 1000*t1,1000*tt/total, total/t2,lineno/t2 ),end = '')
