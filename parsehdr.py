#! /usr/bin/python

import os                                                                       
import sys                                                                      
import time                                                                     
import string                                                                   
#import re                                                                       
import traceback

import email
import email.Header
#import binascii

#mailno=0

def log(level,text):

    if type(text)==unicode:
#	sys.stderr.write("mail2sql[%d] %d: %s\n"%(os.getpid(),3,"log() called with unicode string!"))
#	log_data.append((3,"log() called with unicode string!"))
	text=text.encode("latin2","xmlcharrefreplace")
    print(text)


# inspired by Header.py::__unicode__()
def hdrdecode(h):
#    log(0,"hdrdecode: '%s'" % h)
    if not h:
	return u""
    uchunks = []
    last = None

    for s,enc in email.Header.decode_header(h):
	if uchunks:
	    if last not in (None, 'us-ascii'):
		if enc in (None, 'us-ascii'):
		    uchunks.append(u' ')
	    else:
		if enc not in (None, 'us-ascii'):
		    uchunks.append(u' ')
	last=enc
	try:
	    uchunks.append(unicode(s,enc or "latin2"))
	except:
	    uchunks.append(unicode(s,"latin2"))
    return u''.join(uchunks)



def cleanupspaces(s,split=0):
    q=0
    e=0
    z=0
    a=0
    s2=""
    comm=""
    addr=""
    p=0
    for c in s:
	if e:
	    e=0
	elif c=='\\':
	    e=1
	else:
	    if c=='"':
		q=1-q
	    if q==0:
		if c=='(':
		    z+=1
		elif c==')':
		    z-=1
		    if split:
			comm+=c
			continue
		elif c=='<':
		    a+=1
		elif c=='>':
		    a-=1
		    if split:
			addr+=c
			continue
		elif c=='\t' or c=='\n' or c=='\r':
		    c=' '
		if c==' ' and p==c and z==0 and a==0:
		    continue
	if split:
	    if z>0:
	        comm+=c
	        continue
	    if a>0:
	        addr+=c
	        continue
	s2+=c
	p=c
    if e:
	log(1,"WARNING! escape?")
    if q:
	log(1, "WARNING! doublequote?")
    if z!=0:
	log(1, "WARNING! parenthesis?")
#	print "!%d!s='"%(mailno) +s+ "'"
    if split:
	return (s2.strip(),comm,addr)
    return s2.strip()

def splithdr(s,sep=' '):
    sa=[]
    q=0
    e=0
    z=0
    s2=""
    for c in s:
	if e:
	    e=0
	elif c=='\\':
	    e=1
	else:
	    if c=='"':
		q=1-q
	    if q==0:
		if c=='(':
		    z+=1
		elif c==')':
		    z-=1
		elif z==0 and c==sep:
		    sa.append(s2.strip())
		    s2=""
		    continue
	s2+=c
    if z!=0:
	log(1, "WARNING! parenthesis?")
    sa.append(s2.strip())
    return sa

def qstrip(s):
    try:
	while s[0]==' ':
	    s=s[1:]
	while s[-1]==' ':
	    s=s[:-1]
	if s[0]=='"' and s[-1]=='"':
	    s=s[1:-1]
	if s[0]=="'" and s[-1]=="'":
	    s=s[1:-1]
#	if s[0]=='<' and s[-1]=='>':
#	    s=s[1:-1]
	if s[0]=='(' and s[-1]==')':
	    s=s[1:-1]
	if s[0]=='[' and s[-1]==']':
	    s=s[1:-1]
	if s[0]=='{' and s[-1]=='}':
	    s=s[1:-1]
	while s[0]==' ':
	    s=s[1:]
	while s[-1]==' ':
	    s=s[:-1]
    except:
	log(1, "QSTRIP:"+s+" EXC:%s" % (traceback.format_exc()) )
    return s

def isatext(s):
    for c in s:
	if not (c in "!#$%&'*+-/=?^_`{|}~0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"):
#	    print "!isatext: "+c
	    return 0
    return 1

def isemailaddr(s):
    if s.find('@')<0:
	if s=="<>":
	    return s
	if s.upper()=="MAILER-DAEMON":
	    return "MAILER-DAEMON"
	return None
    if s[0]=='<':
	if s[-1]=='>':
	    s=s[1:-1].rstrip(' ')
    kukac=0
    for c in s:
	if not (c in ".@_~=!#$%&*/+-0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"):
	    return None
	if c=='@':
	    kukac+=1
    if kukac==1:
	return s
    return None


addrlist={}

def add_addr(hdr,addr,nev):
#    print("ADDR[%s] %s '%s'"%(hdr,addr,nev))
    if nev:
      print("NAME[%s]=%s"%(hdr,nev))
    addr=addr.lower()
    if addr in addrlist:
	a,n,h=addrlist[addr]
	if nev and nev!=n:
	    if hdr=="from" or n==None:
		n=nev
	addrlist[addr]=(a,n,h+","+hdr)
    else:
	print("ADDR[%s]=%s"%(hdr,addr))
	addrlist[addr]=(addr,nev,hdr)

################################ MAIN ################################


try:
  f=open("HAM.mbox")

#  has_sender=0
  has_error=0
#  has_from=0
#  has_rcvd=0
  in_hdr=1
  hdr=""
  for rawline in f:
    try:
      if in_hdr:
	line=rawline.rstrip()
	if line=="":
	    in_hdr=0
	elif line[0] in ['\t',' ']:
	    hdr+=line
	    continue

	if hdr:
	    try:

		hdrname,hdrbody = hdr.split(':',1)
		hdrname=hdrname.lower()
#		print(hdrname)
		if hdrname in ["from","to","cc","bcc","reply-to"]:
		    sa=splithdr(cleanupspaces(hdrbody),',')
#		    has_from+=len(sa)
		    for aa in sa:
			cim=None
			nev=""
			if aa:
			  if aa.find(' ')<0 and aa.find('<')<0:
			    cim=isemailaddr(aa)
			  else:
			    nev,comm,addr=cleanupspaces(aa,1)
#			    log(0,hdrname+": COMM=%s ADDR=%s NEV=%s" % (comm,addr,nev) )
			    if addr:
				cim=isemailaddr(addr)
				if cim:
				    #log(0,hdrname+": "+cim)
				    if nev:
					nev=qstrip(cleanupspaces(nev))
					nev=qstrip(hdrdecode(nev))
				#	if nev!=cim:
				#	    log(0,hdrname+"_name: "+nev)
				else:
				    log(1, "HIBAS:"+addr+" RAW:"+aa)
				    has_error+=1
			    else:
				cim=isemailaddr(nev)
				if cim:
				#    log(0,hdrname+": "+cim)
				    nev=qstrip(comm)
				#    if nev and nev!=cim:
				#	log(0,hdrname+"_name: "+comm)
				else:
				    log(1, "HIBAS:"+nev+" RAW:"+aa)
				    has_error+=1
			
			if cim:
			    if nev and nev!=cim:
#				log(0,hdrname+": ["+nev+"] <"+cim+">")
				add_addr(hdrname,cim,nev)
			    else:
#				log(0,hdrname+": <"+cim+">")
				add_addr(hdrname,cim,None)

#			if comm:
#			    print hdrname
#		    if len(sa)!=1:
#			print sa
#		    else:
#			print sa[0]
	    except:
		log(1, "INVALID:"+hdr+" EXC:%s" % (traceback.format_exc()) )
#		traceback.print_exc()
	hdr=line
	continue

      if rawline[0:5]=="From ":
	in_hdr=1
	hdr=""

    except:
      log(1, "mainloop EXC:%s" % (traceback.format_exc()) )
      pass

except:
  log(1, "main EXC:%s" % (traceback.format_exc()) )

