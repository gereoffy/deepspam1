INSTALL
=======
A hasznalathoz eleg csak a milter modult (deepspam3.py) futtatni egy szerveren.
A parameterek egyelore bele vannak drotozva, ami lenyeges az a socket, by default a 1080-as TCP porton figyel.

DEPENDENCY:
- Python 3.6+  (3.8/3.10 gyakran tesztelve)
- tensorflow 2.x
- numpy
- h5py   (a regi model formatumhoz kell csak, v9-hez mar nem)
- GPU _nem_ szukseges hozza, eleg gyors mar CPU-n is

Postfix konfiguracio:
  smtpd_milters = inet:127.0.0.1:1080      (vagy ha masik gepen fut a milter, akkor annak az IP-je)
  milter_default_action = accept
(a 2. sor azert kell, hogy hiba eseten ne dobalja vissza a leveleket)

Spamassassin konfiguracio:  (pl. /var/lib/spamassassin/3.004000/deepspam.cf fileba, de mehet az user_prefs-be is)

header   DEEPSPAM_HAM       X-deepspam =~ /^ham/i
describe DEEPSPAM_HAM       DeepSpam probability<2%
score    DEEPSPAM_HAM       -3

header   DEEPSPAM_MHAM       X-deepspam =~ /^maybeham/i
describe DEEPSPAM_MHAM       DeepSpam probability<10%
score    DEEPSPAM_MHAM       -2

header   DEEPSPAM_M2HAM       X-deepspam =~ /^20ham/i
describe DEEPSPAM_M2HAM       DeepSpam probability<20%
score    DEEPSPAM_M2HAM       -1

header   DEEPSPAM_SPAM       X-deepspam =~ /^spam/i
describe DEEPSPAM_SPAM       DeepSpam probability>98%
score    DEEPSPAM_SPAM       6

header   DEEPSPAM_MSPAM       X-deepspam =~ /^maybespam/i
describe DEEPSPAM_MSPAM       DeepSpam probability>90%
score    DEEPSPAM_MSPAM       4

header   DEEPSPAM_M2SPAM       X-deepspam =~ /^80spam/i
describe DEEPSPAM_M2SPAM       DeepSpam probability>80%
score    DEEPSPAM_M2SPAM       2
3