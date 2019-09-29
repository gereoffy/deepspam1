
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

from html2text import HTML2Text

try:
  # Python 2.6-2.7 
  from HTMLParser import HTMLParser
except ImportError:
  # Python 3
  from html.parser import HTMLParser

html_parser = HTMLParser()

def html2text(data):
    #text_maker = html2text.HTML2Text()
    text_maker = HTML2Text()
    #help(text_maker)
    text_maker.ignore_links = True
    text_maker.ignore_images = True
    text_maker.ignore_anchors = True
    text_maker.ignore_links = True
    text_maker.unicode_snob = True
    text_maker.body_width = 0
    text_maker.decode_errors = "ignore"
    text_maker.bypass_tables = False
#    return text_maker.handle(text_maker.unescape(data))
    return text_maker.handle(data)
#    return text_maker.unescape(data)

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
TAG_RE4 = re.compile(r'[-+$_.a-z0-9]*@[-.a-z0-9]*.[a-z][a-z]*')
TAG_RE5 = re.compile(r'$[0-9][0-9]*')
TAG_RE6 = re.compile(r'[-0-9a-z][-0-9a-z][-0-9a-z]*\.[-0-9a-z][-0-9a-z][-0-9a-z]*\.[-0-9a-z][-0-9a-z][-0-9a-z]?')

def remove_url(text):
    text=TAG_RE3.sub('httpurl', text)
    text=TAG_RE5.sub('dollarandnumber', text)
    text=TAG_RE6.sub('domainname', text)
    return TAG_RE4.sub('emailaddress', text)

def remove_accents(input_str):
    try:
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return nfkd_form.encode('ASCII', 'ignore')
#        return nfkd_form
    except:
        return input_str.encode('ASCII', 'ignore')


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
    print(type(msg))

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
    ctyp=p.get_content_type().lower()
    disp=p.get_content_disposition()
#    print((ctyp,disp,charset))
    if ctyp.split('/')[0]=="text" and disp!="attachment":
#      print(ctyp)
#      if ctyp.find("rfc")>=0:
#        continue
      try:
        data=p.get_payload(decode=True).decode(charset, 'mixed').lower()
        data=xmldecode(data) # plaintextre is rafer...
        if ctyp=="text/html" or ctyp=="text/xml" or data.find('<')>=0 and (data.find("<body")>=0 or data.find("<img")>=0 or data.find("<style")>=0 or data.find("<center")>=0 or data.find("<a href")>=0):
#          print(data.encode("iso8859-2"))
#          print("parsing html...")
          data=html2text(data)
          text.append(data)
        elif ctyp=="text/plain":
          text.append(data)
      except:
        eprint(traceback.format_exc())
  return text



def tokenize(s,vocab):
    ss=""
    tokens=[]
    vtokens=[]
#    print(s.encode("utf-8"))
    s=remove_url(s)
    s=html_parser.unescape(s)
#    print(s.encode("utf-8"))
    #s1=s.encode('ASCII', 'ignore').decode('ASCII', 'ignore')
    #if s==s1:
    #  s=s.lower()
    #else:
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
      if len(t)>=4:
        if t in vocab:
          vtokens.append(t)

#    print(tokens)

#    for t in tokens:
#    if n>=10 and nn>=5:
    return (vtokens,tokens)


