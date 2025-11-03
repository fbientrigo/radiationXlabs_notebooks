#! /usr/bin/env python
# pretty basic routine for radiation tests DAQ.

import serial
import list_ports
from DMM_module import DMM
from ARDU_module import ARDU
from verDAQ8_module import VERDAQ8
from datetime import datetime

from time import sleep
import logging
import sys

import signal
import sys
import os

import pandas as pd
verdaq_COM = "COM9"
arduino_COM = "COM6"
def signal_handler(sig, frame):
    print('Going out of verdaq DAQ, au revoir!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

rootdir = "data_run"
fname = rootdir + "/daqlog"
date = datetime.now().strftime("%Y_%m_%d_%H%M%S")
fname = fname + "_" + date + ".log"
datadirC = rootdir + "/DMM_data/"
MINI = 1.05
MAXI = 1.3
MAXCNTLOW = 2
MAXCNTHIGH = 2

def is_current_low():
    global MINI, MAXCNTLOW, datadirC
    fnameC = datadirC + os.listdir(datadirC)[-1]
    dtypes = {0 : 'float64', 1: 'float32', 2: 'float32'}
    df = pd.read_csv(fnameC,delimiter=' ',header=None, dtype=dtypes, parse_dates=[0],on_bad_lines='skip')#error_bad_lines=False)
    dataC = df.tail(MAXCNTLOW)
    cnt = len(dataC[MINI > dataC[1]])
    if cnt >= MAXCNTLOW:
        return True
    return False

def is_current_high():
    global MAXI, MAXCNTHIGH, datadirC
    fnameC = datadirC + os.listdir(datadirC)[-1]
    dtypes = {0 : 'float64', 1: 'float32', 2: 'float32'}
    df= pd.read_csv(fnameC,delimiter=' ',header=None, dtype=dtypes, parse_dates=[0],on_bad_lines='skip')#error_bad_lines=False)
    dataC = df.tail(MAXCNTHIGH)
    cnt = len(dataC[dataC[1] > MAXI]) 
    if cnt >= MAXCNTHIGH:
        return True
    return False


logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename=fname,
                    filemode='w',
                    level=logging.DEBUG)
#logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logFormatter = logging.Formatter('%(asctime)s %(message)s')
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
logging.getLogger().addHandler(consoleHandler)

log = logging.getLogger("launchDAQ")

class SNUMS:
    SNUM_CPLD = 5100029
    SNUM_ZYNQ = 6894024
    SNUM_ARDU = 1000001
    
log.info("#############Starting DAQ for the Radiation Test at CHARM########")

ports = list_ports.serial_ports()
log.info("available ports: " )
for p in ports:
    log.info(p)
################### MAIN LOOP ################
### CONNECTING DEVICES ####
log.info("connecting devices...")
dmmzynq = None
dmmcpld = None
arduino = None
ports = list_ports.serial_ports()
#for p in ports:
#    if p == 'COM8':
#        continue
#    #only arduino + verDAQ8 here
#    ardu = ARDU(p)
#    match dev.snum: 
#        case SNUMS.SNUM_ZYNQ:
#            dmmzynq = dev 
#        case SNUMS.SNUM_CPLD:
#            dmmcpld = dev
#        case SNUMS.SNUM_ARDU:
#            arduino = dev
arduino = ARDU(arduino_COM)
arduino.setON_verdaq()
sleep(10)
del arduino
verdaq = VERDAQ8(verdaq_COM,rootdir)
#if (arduino and verdaq):
if (verdaq):
    log.info("only verdaq online.")
else:
    log.info("ERROR: device missing")

def check_current():
    global verdaq, arduino, log
    try:
        if is_current_low():
            
            log.error("verdaq current low, sending power cycle")
            arduino = ARDU(arduino_COM)
            arduino.powercycle_V()
            del verdaq
            del arduino
            verdaq = VERDAQ8(verdaq_COM,rootdir)
            return True
        if is_current_high():
            
            log.error("verdaq current high, sending power cycle")
            arduino = ARDU(arduino_COM)
            arduino.powercycle_V()
            del verdaq
            del arduino
            verdaq = VERDAQ8(verdaq_COM,rootdir)
            return True
    except:
        print("Error reading current file. skipping")

    return False

#for k in range(5):
while (True):
    if (check_current()):
        continue
    ret = verdaq.read_event()
    if (ret):
        arduino = ARDU(arduino_COM)
        del verdaq
        log.error("verdaq not responding, sending power cycle, error_code:"+str(ret))
        arduino.powercycle_V()
        del arduino
        verdaq = VERDAQ8("COM8",rootdir)
        sleep(3)
        continue
    log.info("event stored")

 
