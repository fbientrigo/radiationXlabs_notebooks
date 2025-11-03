import serial
import list_ports
from time import sleep, time
from datetime import datetime
import signal
import sys
import os

rootdir = "data_run"

def signal_handler(sig, frame):
    print('Going out of DMM module, au revoir!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class DMM:
    idx = 0
    snum = 0
    sp = None
    fidx = 0
    rootdir = "data_debug" 
    fname = "DMM_data/dmm_data"
    MAXFSIZE = 0.01
    outfile = None
    def sendCMD(self,cmd):
        self.sp.write(cmd.encode())
        res = self.sp.readline()
        res = self.sp.readline()

        #print(res.decode())
        #if res.decode()[:2] != '=>':
        #    print("ERROR sending " + cmd)
        #    exit()
        return res.decode()

    def sendQUERY(self,cmd):
        #print(datetime.now().strftime("%Y %m %d %H:%M:%S") + ": sending query DMM: " + cmd)
        self.sp.write(cmd.encode())  
        res = self.sp.readline(), self.sp.readline()
        if res[0].decode()[:2] == '?>':
            print("ERROR sending " + cmd)
            exit()
        return res[0].decode()

    def __init__(self,portn,rootdir=None):
        try :
            self.sp = serial.Serial(str(portn),timeout = 1)
            sleep(2)
        except :
            print("ERROR: port named: " + portn + " connection failed.")
            exit()

        self.idx = DMM.idx
        DMM.idx += 1
        print("TRYING DMM on port " + str(self.sp.name))
        
        #res = self.sendCMD("*IDN?")
        #print(res)
        #self.snum = int(res.split(", ")[2])
        #if self.snum == 1000001:
        #    print("DMM " + str(self.idx) + " serial: " + str(self.snum))
        #    print("ARDUINO HERE")
        #    self.sp.close()
        #    return


        if (rootdir != None):
            self.rootdir = rootdir
            date = datetime.now().strftime("%Y_%m_%d_%H%M%S")
            self.fname = self.rootdir + "/" + self.fname
            self.fname += str(self.snum) + "_" + date + "_" + "{:05d}.dat".format(self.fidx)
            try:
                self.outfile = open(self.fname,"w")
            except :
                print("ERROR: file:"+self.fname+" for DMM data was not created")
                exit()

        print("DMM " + str(self.idx) + " on port " + str(self.sp.name) + " connected")
        #print("DMM " + str(self.idx) + " serial: " + str(self.snum))
        print("setting default configuration: DC current.")
        self.sendCMD(":FUNC CURR:DC")
        
        #res = self.sendQUERY("*OPC?\r")
        #print(res)
            
    def getValues(self):
        v1 = self.sendCMD(":FETC?\n")
        return (v1)

    def replace_ofile(self):
        self.fidx +=1
        self.fname = self.fname[:len(self.fname)-9] + "{:05d}.dat".format(self.fidx)
        try:
            self.outfile.close()
            self.outfile = open(self.fname,"w")
        except :
            print("ERROR: file:"+self.fname+" for DMM data was not created")
            exit()

    def store_values(self):
        if  os.path.getsize(self.fname)/1000000. > self.MAXFSIZE:
            self.replace_ofile()
        
        idc = self.getValues()
        self.outfile.write(str(time()) + " " + idc + "\n")
        self.outfile.flush()
        print(datetime.now().strftime("%Y %m %d %H:%M:%S") + ": stored values:: " +idc+"\n")


    def __del__(self):
        self.sp.close()
    

if __name__=="__main__":
    #global rootdir

    ports = list_ports.serial_ports()
    print(rootdir)
    dm=DMM("COM11",rootdir)
    if dm.snum == 6894024:
        dmmzynq = dm

    while(True):
        dm.store_values()
        sleep(1)
