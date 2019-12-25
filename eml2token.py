
from __future__ import print_function

#import io
#import os
import sys

#import errno
#import mimetypes
#from html2text import html2text
import re
import traceback


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


import email
import codecs
import unicodedata


from htmlentitydefs import name2codepoint

#def html_unescape1(tag):
#  try:
#    return unichr(name2codepoint[tag])
#  except:
#    return "?"

HTML_RE = re.compile(r'&([^;]+);')

try:
    unichr
except NameError:
    unichr = chr

def html_unescape(mystring):
#  return re.sub('&([^;]+);', lambda m: unichr(name2codepoint[m.group(1)]), mystring)
#  return re.sub('&([^;]+);', lambda m: html_unescape1(m.group(1)), mystring)
#  return HTML_RE.sub(lambda m: html_unescape1(m.group(1)), mystring)
  return HTML_RE.sub(lambda m: unichr(name2codepoint.get(m.group(1),63)), mystring)


def html2text(data):
  in_style=0
  in_script=0
  text=""
  for ret in data.split("<"):
    try:
      tag,txt=ret.split(">",1)
    except:
      text+=ret
      continue
#      print(ret.encode("utf-8"))
#      break
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
      if tag1=="p" or tag1=="br" or tag1=="td" or tag1=="div" or tag1=="li":
        text+="\n"
      text+=txt

#  print(text.encode("utf-8"))
  return text



#last_position = -1

def mixed_decoder(unicode_error):
#    global last_position
    position = unicode_error.start
#    if position <= last_position:
#        position = last_position + 1
#    last_position = position
#    new_char = string[position]
#    print(position)
#    print(type(string))
#    new_char = bytes(string[position])
    new_char = unicode_error.object[position:position+1]
#    print(type(new_char))
#    print(len(new_char))
    new_char = new_char.decode("iso8859-2","ignore")
#    print(type(new_char))
#    print(len(new_char))
    #new_char = u"_"
    return new_char, position + 1

codecs.register_error("mixed", mixed_decoder)


TAG_RE1 = re.compile(r'<[^>]+>')
TAG_RE2 = re.compile(r'\[[^[]+\]')
TAG_RE3 = re.compile(r'https? ?: ?//[-._a-zA-Z0-9/?&=]*')
#TAG_RE4 = re.compile(r'[-+$_.a-z0-9]*@[-.a-z0-9]*.[a-z][a-z]*')
TAG_RE4 = re.compile(r'[-+$_.a-z0-9]*@[-.a-z0-9]*\.[a-z][a-z]*')
TAG_RE5 = re.compile(r'$[0-9][0-9]*')
TAG_RE6 = re.compile(r'[-0-9a-z][-0-9a-z][-0-9a-z]*\.[-0-9a-z][-0-9a-z][-0-9a-z]*\.[-0-9a-z][-0-9a-z][-0-9a-z]?')

def remove_url(text):
    text=TAG_RE3.sub('httpurl', text)
    text=TAG_RE4.sub('emailaddress', text)
    text=TAG_RE6.sub('domainname', text)
    text=TAG_RE5.sub('dollarandnumber', text)
    return text




def remove_accents(input_str):
    s0=input_str.encode('ASCII', 'ignore')
    if input_str==s0.decode('ASCII', 'ignore'):
        return s0
    try:
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return nfkd_form.encode('ASCII', 'ignore')
#        return nfkd_form
    except:
#        return input_str.encode('ASCII', 'ignore')
        return s0


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
#            return unichr(c) # python 2.x ?
            return chr(c) #Python3
    return x # beken hagyjuk

#    r_unescape = re.compile(r"&(#?[xX]?(?:[0-9a-fA-F]+|\w{1,8}));") # ez erre is matchel:   &nbsp;
r_unescape = re.compile(r"&(#[xX]?[0-9a-fA-F]+);") # de nekunk csak az ekezetes betu unikodok kellenek!

def xmldecode(data):
    return r_unescape.sub(replaceEntities, data)

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
    disp=p.get_content_disposition()
#    print((ctyp,disp,charset))
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
          if p>0:
            data=data[p:]
          data=html2text(data)
          text.append(data)
        elif ctyp=="text/plain":
          text.append(data)
      except:
        eprint(traceback.format_exc())
  return text



def tokenize(s,vocab,minlen=4):
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
    s=remove_accents(s).decode('ASCII', 'ignore').lower()
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


