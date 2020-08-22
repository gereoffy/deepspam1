#! /usr/bin/python3


###
### DeepSpam milter filter
###
### Uj verzio, ami a ppymilter-re epul (pure python milter), ehhez nem kell a libmilter, nem hasznal C kodot, jobb a memoriakezelese ( = nem leakel :))
### Csak a ppymilterbase.py file szukseges hozza:  https://raw.githubusercontent.com/agaridata/ppymilter/master/lib/ppymilter/ppymilterbase.py
### Az egesz 1 threadban fut, async modu halozatkezelessel. 64k meretu emailekkel tesztelve kb 40 email/masodperc sebesseget tudott!
### Valoszinuleg csak python3-al mukodik, bar talan atirhato py2-re is, ha van ra igeny.
###


import asyncore, asynchat, socket
import ppymilterbase
import logging
import binascii
import struct
import time

try:
  from io import BytesIO
except:
  from StringIO import StringIO as BytesIO

############################################################################################################################################

import email
from eml2token import eml2str,tokenize,eprint

from ds_model import deepspam_load,deepspam_test
wordmap=deepspam_load()

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

#    print(" ".join(vtokens))
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

############################################################################################################################################



class MyHandler(ppymilterbase.PpyMilter):

#    def __init__(self):
#        print("MyHandler.init!")
#        ppymilterbase.PpyMilter.__init__(self)
#        super().__init__()
#        CanChangeHeaders(self)

    def OnOptNeg(self, cmd, ver, actions, protocol):
        self.CanAddHeaders()
        self.emlcount=0
        self.t=0
#        self.mailfrom = ""
        return super().OnOptNeg(cmd, ver, actions, protocol)

    def OnConnect(self, cmd, hostname, family, port, address):
#        print(hostname)
#        print(address)
        self.mailfrom = address
        return self.Continue()

    def OnHelo(self, cmd, data):
#        print(data)
        return self.Continue()

    def OnResetState(self):
#        print("ResetState called!")
        self.fp = None
        self.bodysize = 0
        self.reject=0

    def OnMailFrom(self, cmd, addr, esmtp_info):
        self.OnResetState()
        self.mailfrom = addr
#        print(addr)
#        print(esmtp_info)
        return self.Continue()

    def OnRcptTo(self, cmd, addr, esmtp_info):
#        print(addr)
#        print(esmtp_info)
        return self.Continue()

    def OnHeader(self, cmd, hdr, data):
        if hdr==b'X-Grey-ng' and data[0:6]==b'REJECT':
            self.reject=1
#        if self.fp:
        if not self.fp:
            self.fp = BytesIO()
            self.emlcount+=1
        self.fp.write(hdr+b': '+data+b'\n')
#        print(hdr)
#        print(data)
        return self.Continue()

    def OnEndHeaders(self, cmd):
        self.fp.write(b'\n')
        return self.Continue()

    def OnBody(self, cmd, data):
#        print(len(data))
#        print(type(data))
        self.fp.write(data)
        self.bodysize += len(data)
        return self.Continue()

    def OnEndBody(self, cmd):
         if not self.fp:
             return self.ReturnOnEndBodyActions([self.Accept()])
         t=time.time()
         self.fp.seek(0)
         msg = email.message_from_binary_file(self.fp) # python 3.2+
         res=do_eml(msg)
         self.t=time.time()-t
         h=[]
         h.append(self.AddHeader('X-deepspam', res))
         h.append(self.Accept())
         return self.ReturnOnEndBodyActions(h)

    def __del__(self):
#        print("__del__ called!")
#        global thread_cnt
#        thread_cnt-=1
        print("__del__ called!     processed: %d (%5.3f)  from: %s"%(self.emlcount,self.t,self.mailfrom))







MILTER_LEN_BYTES = 4  # from sendmail's include/libmilter/mfdef.h

thread_cnt=0

class SecondaryServerSocket(asynchat.async_chat):
#  def __init__(self, *args):
  def __init__(self, sock, addr):
    global thread_cnt
    thread_cnt+=1
    self.t0=time.time()
    print('initing SSS -> %2d      %s'%(thread_cnt,str(addr)))
#    asynchat.async_chat.__init__(self, *args)
    asynchat.async_chat.__init__(self, sock)
    self.__milter_dispatcher = ppymilterbase.PpyMilterDispatcher(MyHandler)
    self.data = None
    self.set_terminator(MILTER_LEN_BYTES)
    self.milterstate=False
#    self.found_terminator = self.read_packetlen


  def __del__(self, *args):
    global thread_cnt
    thread_cnt-=1
    t=time.time()-self.t0
    print('freeing SSS -> %3d   time: %6.3f'%(thread_cnt,t))
#    return asynchat.async_chat.__del__(self, *args)

  def collect_incoming_data(self, data):
    if self.data==None:
      self.data=data
    else:
      self.data+=data
#    print("incoming: %d/%d"%(len(data),len(self.data)))

  def found_terminator(self):
    if not self.milterstate:
      # read packet len:
      packetlen = int(struct.unpack('!I', self.data)[0])
      self.data = None
      self.milterstate=True
      self.set_terminator(packetlen)
      return
    # read packet data:
    inbuff = self.data
    self.data = None
    self.milterstate=False
    self.set_terminator(MILTER_LEN_BYTES)
    # process milter request:
#    print('  <<< ', binascii.b2a_qp(inbuff[:60]))
    try:
      response = self.__milter_dispatcher.Dispatch(inbuff)
    except ppymilterbase.PpyMilterCloseConnection as e:
#      print('Closing connection: ', str(e))
      return self.handle_close()

    if response:
      if type(response) != list:
        response=[response]
      for r in response:
        if isinstance(r, str):
          r=r.encode()
#        print('  >>> ', binascii.b2a_qp(r))
        self.push(struct.pack('!I', len(r))+r)
#    else:
#      print('  >>> None!')

#  def handle_close(self):
#    print("Disconnected!")
#    self.close( )



class MainServerSocket(asyncore.dispatcher):
  def __init__(self, port):
    print('initing MSS')
    asyncore.dispatcher.__init__(self)
    self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
      try:
        self.bind(('',port))
        break
      except:
        time.sleep(1)
      continue
    self.listen(5)
  def handle_accept(self):
    newSocket, address = self.accept( )
#    print("Connected from", str(address))
    SecondaryServerSocket(newSocket,address)


logging.basicConfig(level=logging.DEBUG,
                      format='%(asctime)s %(levelname)s %(message)s',
                      datefmt='%Y-%m-%d@%H:%M:%S')

MainServerSocket(1080)
asyncore.loop()

