import serial
import list_ports
from time import sleep, time
from datetime import datetime
import os
import signal 
import sys

portn = "COM9"
BAUDRATE = 115200
TIMEOUT = 5

sp = serial.Serial(str(portn),baudrate=BAUDRATE,timeout = TIMEOUT)
for i in range(0,3):
    r=sp.read_until(b'\n#-\n',size=4)    
    print(r)