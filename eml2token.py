
from __future__ import print_function

import io
#import os
import sys

import time

#import errno
#import mimetypes
#from html2text import html2text
import re
import traceback

# docx olvasashoz:
import zipfile

try:
  import pdftotext
  pdf_support="pdftotext"
except:
  try:
    import pdfminer.high_level
    pdf_support="pdfminer"
  except:
    pdf_support=None

try:
  from striprtf import rtf_to_text
  rtf_support=1
except:
  rtf_support=0

try:
  from tnefparse import TNEF
  tnef_support=1  # TNEF/HTML support
  if rtf_support:
    try:
      import compressed_rtf
      tnef_support=2  # TNEF/RTF support
    except:
      pass
except:
  tnef_support=0


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


import email
import codecs

from email.header import decode_header,make_header

def hdrdecode(h):
    try:
        return unicode(make_header(decode_header(h.replace("?==?","?= =?"))))
    except NameError:
        pass
    try:
        return str(make_header(decode_header(h)))
    except:
        return h

from htmlentitydefs import name2codepoint

HTML_RE = re.compile(r'&([^;]+);')
HTML_comment = re.compile(r'<!--.*-->',re.DOTALL)
HTML_color = re.compile(r'[^-]color:#ffff*[^0-9a-f]')
HTML_fontsize = re.compile(r'font-size:[0-5]px')

#HTML_color = re.compile(r'color')

try:
  unichr
except NameError:
  unichr = chr

def html_unescape(mystring):
  return HTML_RE.sub(lambda m: unichr(name2codepoint.get(m.group(1),63)), mystring)

def replaceEntities(s):
    x = s.group(0)
    s = s.group(1)
#    print(x)
#    print(s)
    if s[0] == "#":
        if s[1] in ['x','X']:
            c = int(s[2:], 16)
        else:
            c = int(s[1:])
        if c>=128: # ekezetes karakter, nem irasjel
            return unichr(c) # python3-ban chr()
    return x # beken hagyjuk

#    r_unescape = re.compile(r"&(#?[xX]?(?:[0-9a-fA-F]+|\w{1,8}));") # ez erre is matchel:   &nbsp;
r_unescape = re.compile(r"&(#[xX]?[0-9a-fA-F]+);") # de nekunk csak az ekezetes betu unikodok kellenek!

def xmldecode(data):
  return r_unescape.sub(replaceEntities, data)


def html2text(data):
  in_style=0
  in_script=0


#  data=HTML_comment.sub("<comment>",data)
  p=data.find("<!--")
  while p>=0:
    q=data.find("-->",p)
    if q<p:
      data=data[:p]
      break
    data=data[:p]+" HTMLcomment "+data[q+3:]
    p=data.find("<!--",p)


  text=""
  for ret in data.split("<"):
    try:
      tag,txt=ret.split(">",1)
    except:
      text+=ret
      continue
#      print(ret.encode("utf-8"))
#      break
#    print("TAG: '%s'"%(tag))
    try:
      tag1=tag.split()[0].lower()
    except:
#      print("TAG parse error: '%s'"%(tag))
      tag1=""
    if tag1=="style":
      in_style+=1
    if tag1=="/style":
      in_style-=1
    if tag1=="script":
      in_script+=1
    if tag1=="/script":
      in_script-=1
#    print(tag1)
#    print(text)
    if in_style<=0 and in_script<=0:
      if tag1 in ["p","span","div"]:
#        print(tag.lower())
        if HTML_color.search(tag.lower()+";"):
          text+="\nHTMLhiddenWHITE:"
        if HTML_fontsize.search(tag.lower()):
          text+="\nHTMLhiddenFONTSIZE:"
      if tag1=="p" or tag1=="br" or tag1=="td" or tag1=="div" or tag1=="li":
        text+="\n"
      text+=txt

#  print(text.encode("utf-8"))
#  print(text)
  return text



def mixed_decoder(unicode_error):
    position = unicode_error.start
    new_char = unicode_error.object[position:position+1]
    new_char = new_char.decode("iso8859-2","ignore")
#    print(type(new_char))
#    print(len(new_char))
    return new_char, position + 1

codecs.register_error("mixed", mixed_decoder)


TAG_RE1 = re.compile(r'<[^>]+>')
TAG_RE2 = re.compile(r'\[[^[]+\]')
TAG_RE3 = re.compile(r'https? ?: ?//[-._a-zA-Z0-9/?&=]*')
TAG_RE4 = re.compile(r'[-+$_.a-z0-9]*@[-.a-z0-9]*\.[a-z][a-z]*')
TAG_RE5 = re.compile(r'$[0-9][0-9]*')
TAG_RE6 = re.compile(r'[-0-9a-z][-0-9a-z][-0-9a-z]*\.[-0-9a-z][-0-9a-z][-0-9a-z]*\.[-0-9a-z][-0-9a-z][-0-9a-z]?')

def remove_url(text):
    text=TAG_RE3.sub('httpurl', text)
    text=TAG_RE4.sub('emailaddress', text)
    text=TAG_RE6.sub('domainname', text)
    text=TAG_RE5.sub('dollarandnumber', text)
    return text


confusables={}

def load_unicodes(fnev):
    # try to load unicodes.map from file
    for line in io.open(fnev,"rt",encoding="utf-8",errors="ignore"):
        l=line.rstrip("\n\r").split("\t",1)
        confusables[ord(l[0])]=l[1]
    eprint("%d entries loaded from %s file" %(len(confusables),fnev))

import unicodedata

def remove_accents(input_str):
    if len(confusables)==0:
        try:
            load_unicodes("unicodes.map")
        except:
            # generate it with normalize() (without confusables...)
            for ic in range(128,0x20000):
                nfkd_form = unicodedata.normalize('NFKD', chr(ic))
                oc=nfkd_form.encode('ASCII', 'ignore').decode('ASCII', 'ignore')
                if (oc and oc!=chr(ic) and oc!="()"):
                    confusables[ic]=oc
            confusables[215]='x'
            confusables[216]='O' # athuzott 'O' betu
            confusables[248]='o' # athuzott 'o' betu
            confusables[223]='ss' # nemet
            eprint("%d entries generated from unicodedata.normalize" %(len(confusables)))
    return "".join(confusables.get(ord(x),"") if ord(x)>=128 else x for x in input_str)



#    xmlcharref = Regex(r'&#\d+;')
#    xmlcharref.setParseAction(lambda t: '\\u' + hex(int(t[0][2:-1]))[2:]) 
#    return xmlcharref.transformString(data) 

def eml2str(msg):
  if type(msg)==bytes:
    msg = email.message_from_bytes(msg)
  elif type(msg)==str:
    msg = email.message_from_string(msg)
  elif type(msg)!=email.message.Message:
    eprint(type(msg))

  text = []
  textlen=0
  #pp = msg.get_payload()
  for p in msg.walk():
#    print p.get_content_type()
    charset=p.get_content_charset("utf-8")
#    print("charset='%s'"%charset)
    if not charset:
      charset="iso8859-2"
    elif charset=="cp-850":
      charset="cp850"
    elif charset=="_iso-2022-jp$esc":
      charset="iso-2022-jp"
    elif charset=="iso-8859-8-i":
      charset="iso-8859-8"
    elif charset=="windows-874":
      charset="cp874"
    elif charset=="x-mac-ce":
      charset="maccentraleurope"
    elif charset[0:4]=="utf8":
      charset="utf-8"
    ctyp=p.get_content_type().lower()
    fnev=hdrdecode(str(p.get_filename())).lower()
    disp=p.get_content_disposition()
#    print((ctyp,disp,fnev))
    if ctyp.split('/')[0]=="text" and disp!="attachment":
#      print(ctyp)
#      if ctyp.find("rfc")>=0:
#        continue
      try:
        data=p.get_payload(decode=True)
        try:
          data=data.decode(charset, 'mixed')
        except:
          data=data.decode("utf-8", 'mixed')
        data=xmldecode(data) # plaintextre is rafer...
        ldata=data.lower()
        if ctyp=="text/html" or ctyp=="text/xml" or data.find('<')>=0 and (ldata.find("<body")>=0 or ldata.find("<img")>=0 or ldata.find("<style")>=0 or ldata.find("<center")>=0 or ldata.find("<a href")>=0):
#          print(data.encode("iso8859-2"))
#          print("parsing html...")
          p=ldata.find("<body")
          if p>0: data=data[p:]
          data=html2text(data)
#          text.append(data)
          text=[data]     ### FIXME!?   prefer html over txt!
        elif ctyp=="text/plain":
          text.append(data)
        if textlen<len(data):
          textlen=len(data)
      except:
        eprint(traceback.format_exc())
    elif textlen<200:
      s=""
      t0=time.time()
      try:
        if (ctyp=="application/pdf" or fnev.endswith(".pdf")) and pdf_support:
          eprint("PDF: parsing file: "+fnev)
          if pdf_support=="pdfminer":
            s=pdfminer.high_level.extract_text( io.BytesIO(p.get_payload(decode=True)) , maxpages=3 )
          elif pdf_support=="pdftotext":
            pdf = pdftotext.PDF(io.BytesIO(p.get_payload(decode=True)))
            for page in pdf:
              s=str(page)
              if len(s)>200:
                break
        elif (ctyp=="application/rtf" or fnev.endswith(".rtf")) and rtf_support:
          eprint("RTF: parsing file: "+fnev)
          s = rtf_to_text(p.get_payload(decode=True).decode("utf-8","ignore"))
        elif ctyp=="application/vnd.openxmlformats-officedocument.wordprocessingml.document" or fnev.endswith(".docx"):
          eprint("DOCX: parsing file: "+fnev)
          zipf=zipfile.ZipFile(io.BytesIO(p.get_payload(decode=True)))
          html=zipf.read('word/document.xml').decode("utf-8")
          for ret in html.split("<"):
            try:
                tag,txt=ret.split(">",1)
                tag1=tag.split()[0]
            except:
                continue
            if tag1=="w:t":
                s+=txt
            elif tag1 in ["w:tab","w:br","w:cr","w:p"]:
                s+="\t"
        elif (ctyp=="application/ms-tnef" or fnev=="winmail.dat") and tnef_support:
#          print("TNEF: parsing file: "+fnev+" from "+msg.get("Message-id","N/A"))
          eprint("TNEF: parsing file: "+fnev)
          tnefobj = TNEF(p.get_payload(decode=True))
          tnefcp=tnefobj.codepage if tnefobj.codepage else "cp1250"
#          if tnefobj.body:
#              print("TNEF.raw:  %d" %(len(tnefobj.body)))
          if tnefobj.htmlbody:
#              print("TNEF.html: %d" %(len(tnefobj.htmlbody)))
#              print(type(tnefobj.htmlbody))
#              if b"charset=utf-8" in tnefobj.htmlbody:
              try:
                  s=html2text(tnefobj.htmlbody.decode("utf-8","strict"))
#                  print("UTF8 detected in TNEF/HTML...")
              except:
                  s=html2text(tnefobj.htmlbody.decode(tnefcp,"ignore"))
          elif tnef_support>1 and tnefobj.rtfbody:
#              print(type(tnefobj.rtfbody))
#              print("TNEF.rtf:  %d" %(len(tnefobj.rtfbody)))
              s = rtf_to_text(tnefobj.rtfbody.decode(tnefcp,"ignore"))
        t0=time.time()-t0
#        print(s)
        if len(s)>50:
          eprint("parsed: %d chars, %d ms"%(len(s),t0*1000))
          text.append(s)
      except:
        eprint(traceback.format_exc())
  return text



def tokenize(s,vocab,minlen=1):
    ss=""
    tokens=[]
    vtokens=[]
#    print(s.encode("utf-8"))
    s=remove_url(s)
#    s=html_parser.unescape(s)
    s=html_unescape(s)
#    print(s.encode("utf-8"))
#    s1=s.encode('ASCII', 'ignore').decode('ASCII', 'ignore')
#    if s==s1:
#      s=s.lower()
#    else:
#    s=remove_accents(s).decode('ASCII', 'ignore').lower()
    s=remove_accents(s).lower()
#    print(type(s))
#    s=str(s)
#    print(s.encode("utf-8"))
#    print(html_parser.unescape(s).encode("utf-8"))
#    print(s)
    lastc=' '
    for c in s:
#        print(type(c))
#        if (c>=ord('a') and c<=ord('z')) or c==ord('!') or c==ord('-'):
#        if (c>='a' and c<='z') or c=='-':
        if (c>='0' and c<='9'):
            if lastc!=' ' and lastc!='#':
              ss+=' '
            c='#'
            ss+=c
        elif (c>='a' and c<='z'):
            if lastc=='#':
              ss+=' '
            ss+=c
#        elif c!=lastc and c in ['!',',',';',':','.']:
        elif c!=lastc and c in ['!',';','.']:
            ss+=' '+c+' '
#        elif (c<'0' or c>'9') and c!='-' and c!='_' and c!="'":  # aposztrof kell az angol didn't stb miatt...
        elif (c<'0' or c>'9') and c!='-' and c!='_':
            ss+=' '
        lastc=c

#    print(ss.encode("utf-8"))

    for t in ss.strip().split():
#      print(t)
#        if len(t)<3 or len(t)>20:
#            continue
        # not number :)
#        t=t.lower()
      tokens.append(t)
      if len(t)>=minlen:
        if t in vocab:
          vtokens.append(t)

#    print(tokens)

#    for t in tokens:
#    if n>=10 and nn>=5:
    return (vtokens,tokens)


