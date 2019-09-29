INSTALL
=======
A hasznalathoz eleg csak a milter modult (deepspam.py) futtatni a mailserveren.
A parameterek egyelore bele vannak drotozva, ami lenyeges az a socket, by default a 1080-as TCP porton figyel.
Indulaskor betolti es elemzi a milter.eml filet ami egy teszt spam level, ha ez sikerul utana indul csak a milter resz.
(ha csak tesztelgetni akarod, akkor a miltert ki lehet kommentezni es a milter.eml-t kell kicserelni a teszt levelre)

DEPENDENCY:
- Python 3.x  (3.5, 3.6 tesztelve)
- pymilter    (python 3.x-hez pip-el nekem nem fordul, de kezzel a forrasbol a milter.patch alkalmazasa utan igen)
- numpy
- html2text
- h5py   (3-as pythonhoz lehet pickle formatumu modelt is menteni, akkor ez nem szukseges)
- Keras  (pip3 install keras) - a v2.3.0-val nem mukodik, mert van benne egy multi threading bug!
- Tensorflow (elvileg Theanoval is mukodhet, de nem teszteltem) - ha regi a CPU (nincs AVX/AVX2) akkor max 1.5-os verzio hasznalhato!
- GPU _nem_ szukseges hozza (kb 6-8ms 1 level ellenorzese CPU-val), de ha megis van, akkor CUDA8 + CuDNN + tensorflow-gpu kell a hasznalatahoz 
  (de ha sajat modelt akarsz gyartani (learn/*) akkor viszont erosen ajanlott egy izmosabb GPU nagyon sok memoriaval! a 1080ti-vel is 20-60 perc egy menet...)


Postfix konfiguracio:
  smtpd_milters = inet:127.0.0.1:1080
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