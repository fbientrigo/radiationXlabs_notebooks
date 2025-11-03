

import signal
import sys
import os
import serial
from datetime import datetime
from time import time, sleep
import logging


portn="COM10"
BAUDRATE = 115200
TIMEOUT = 2
try :
    sp = serial.Serial(str(portn), baudrate=BAUDRATE, timeout = TIMEOUT)
except :
    exit()
cnt = 0
# Leer secuencia que se espera tarjeta envie al inicio (en bytes)

for i in range(0,20):
    res = sp.read(1)

    if(res.decode() == '\n'):
        res = sp.read(14)
        
        break;
print(res.decode()[3])
print(res.decode()[4])
print(res.decode()[8])
print(res.decode()[9])
print(res)
start_time = time()
