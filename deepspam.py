#! /usr/bin/python3


###
### DeepSpam milter filter
###
### Ez a regi verzio, ami pymilter-re epul, ami a libmilter C wrappere.
### Python3 eseten az 1.0.4 verzio nem jo, mert az meg nem tamogatja a 8 bites fejleceket, csak a github-os kod: https://github.com/sdgathman/pymilter
###


import sys
import os
import errno
import mimetypes
import traceback
#import mime
import Milter


try:
  from io import BytesIO
except:
  from StringIO import StringIO as BytesIO

import email
from eml2token import eml2str,tokenize,eprint

from ds_model_queue import deepspam_load,deepspam_test
wordmap=deepspam_load()

############################################################################################################################################


def do_eml(msg):
#  # jobb ha bytes-ban kapja meg a raw levelet, mert az utf8 karakterek kulonben elcseszodhetnek! pl. sql_0000022480.eml ahol keverve van htmlentity es utf8 text/plain-ben!
#  if type(eml)==bytes:
#    msg = email.message_from_bytes(eml)
#  else:
#    msg = email.message_from_string(eml)
#  try:
#    print len(eml)
    vtokens=[]
    tokens=[]
    for text in eml2str(msg):
      if text.find('pam detection software, running on the system')>=0:
        continue
      t=" ".join(text.replace('"',' ').split())
#      print(t.encode("utf-8"))
      if(len(t)>10):
#        print(str(label)+" "+t.encode("utf-8"))
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
#    print("%d%%"%(res))
    try:
        f=open("deepspam.res","at")
        f.write("%3d%%:"%(res)+" ".join(tokens)+"\n")
        f.close()
    except:
        pass
    if res<2:
        return "ham %d%%"%(res)
    if res<10:
        return "maybeham %d%%"%(res)
    if res<20:
        return "20ham %d%%"%(res)
    if res>98:
        return "spam %d%%"%(res)
    if res>90:
        return "maybespam %d%%"%(res)
    if res>80:
        return "80spam %d%%"%(res)
    return "dunno %d%%"%(res)


class deepspamMilter(Milter.Milter):

  def __init__(self):
    self.mailfrom = None
    self.fp = None
    self.bodysize = 0
    self.id = Milter.uniqueID()
    self.user = None
    self.reject=0

  def envfrom(self,f,*str):
    self.fp = BytesIO()
    self.mailfrom = f
    self.bodysize = 0
    self.reject=0
    return Milter.CONTINUE

  def header(self,name,val):
    if name=="X-Grey-ng" and val[0:6]=="REJECT":
        self.reject=1
    if self.fp:
      try:
        self.fp.write(("%s: %s\n" % (name,val)).encode())  # python2, sima utf8. py2 alatt elvileg tamogatott a surrogate is, de azt ugyis csak az unreleased pymilter tudja
      except:
        try:
          self.fp.write(("%s: %s\n" % (name,val)).encode(encoding='ascii',errors='surrogateescape'))  # python3,  speci (surrogate escaped) utf8 ami 8 bites asciit tarol
        except:
          eprint("DEEPSPAM: Exception at header(%s) !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"%(name))
          eprint(traceback.format_exc())
    return Milter.CONTINUE

  def eoh(self):
    if not self.fp: return Milter.TEMPFAIL	# not seen by envfrom
    self.fp.write(b'\n')
    return Milter.CONTINUE

  def body(self,chunk):		# copy body to temp file
    if self.fp:
      self.fp.write(chunk)	# IOError causes TEMPFAIL in milter
      self.bodysize += len(chunk)
    return Milter.CONTINUE

  def eom(self):
    if not self.fp: return Milter.ACCEPT
    try:
      self.fp.seek(0)
      print("PARSING %d body chars" % self.bodysize)
      try:
        msg = email.message_from_binary_file(self.fp) # python 3.2+
      except:
        msg = email.message_from_file(self.fp) # python2
      res=do_eml(msg)
      print("X-deepspam: "+res)
      self.addheader("X-deepspam",res)
    except:
      eprint("DEEPSPAM: Exception at eom() !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
      eprint(traceback.format_exc())
#    if self.reject:
#      self.setreply('541','5.7.1','Sorry, your address is already blocked for sending spam/virus, contact postmaster')
#      return Milter.REJECT
    return Milter.ACCEPT	# ACCEPT modified message

  def close(self):
    sys.stdout.flush()		# make log messages visible
    if self.fp:
      self.fp.close()
    return Milter.CONTINUE

  def abort(self):
    print("abort after %d body chars" % self.bodysize)
    return Milter.CONTINUE



#res=do_eml("From hello world\nJozsika\n\njkhdsjkdhas\n")


# TESTING
try:
  fp=open("milter.eml","rb")
  #msg = mime.message_from_file(fp)
  #print(type(fp))
  try:
    msg = email.message_from_binary_file(fp)
  except:
    msg = email.message_from_file(fp)
  res=do_eml(msg)
  print("X-deepspam: "+res)
except:
  print("missing/bad milter.eml -> skipping self-test!")

# MILTER MODE
Milter.factory = deepspamMilter
Milter.set_flags(Milter.ADDHDRS)
Milter.set_exception_policy(Milter.ACCEPT)
sys.stdout.flush()
# Milter.runmilter("deepspam","/var/spool/postfix/var/run/deepspam",240)
Milter.runmilter("deepspam","inet:1080",240)

