import serial
import list_ports
from time import sleep, time
from datetime import datetime
import os
import signal 
import sys

rootdir = "data_run"
COM = "COM8"

def signal_handler(sig, frame):
    print('Going out of verdaq8 module, au revoir!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


class VERDAQ8:
    evtcnt = 0
    idx = 0
    snum = 0
    sp = None
    dataframe = []
    rootdir = "data_debug" 
    fname = "/VERDAQ8_data/verDAQ8_data"
    fidx  = 0
    BAUDRATE = 115200
    TIMEOUT  = 15
    MAXFSIZE = 10
    outfile = None
    MAXREADTIME = 100
    MAXWAITCNT = 15
    MAXWAITTIME = 40
    def sendCMD(self,cmd):
        self.sp.write(cmd.encode())
        res = self.sp.readline()
        if res.decode()[:2] != '=>':
            print("ERROR sending " + cmd)
            exit()
        return res.decode()

    def sendQUERY(self,cmd):
        print("sending query to ARDU: " + cmd)
        self.sp.write(cmd.encode())  
        res = self.sp.readline(), self.sp.readline()
        if res[0].decode()[:2] == '?>':
            print("ERROR sending to ARDU" + cmd)
            exit()
        return res[0].decode()

    def __init__(self,portn,rootdir=None):
        try :
            self.sp = serial.Serial(str(portn),baudrate=self.BAUDRATE,timeout = self.TIMEOUT)
        except :
            print("ERROR: port named: " + portn + " connection failed.")
            exit()


        if (rootdir != None):
            self.rootdir = rootdir

            date = datetime.now().strftime("%Y_%m_%d_%H%M%S")
            self.fname = self.rootdir + self.fname
            self.fname += "_" + date + "_" + "{:05d}.dat".format(self.fidx)
            try:
                self.outfile = open(self.fname,"w")
            except :
                print("ERROR: file:"+self.fname+" for verDAQ8 data was not created")
                exit()

        print("VEDAQ8 " + str(self.idx) + " on port " + str(self.sp.name) + " connected")
        self.sp.reset_input_buffer() 

    def print_data(self):
        for line in self.dataframe:
            print(line.strip())

    def replace_ofile(self):
        self.fidx +=1
        self.fname = self.fname[:len(self.fname)-9] + "{:05d}.dat".format(self.fidx)
        try:
            self.outfile.close()
            self.outfile = open(self.fname,"w")
        except :
            print("ERROR: file:"+self.fname+" for verDAQ8 data was not created")
            exit()

    def store_event(self):
        if  os.path.getsize(self.fname)/1000000. > self.MAXFSIZE:
            self.replace_ofile()

        for line in self.dataframe:
            self.outfile.write(line)
    def wait_init_seq_2(self):
        try:
            res=self.sp.read_until(b'\n#-\n',size=4)
        except UnicodeDecodeError:
            print ("Unicode error, res: " + str(res))
            return 0

        print ("initial seq found " + str(res))
        return 0
    def wait_initial_seq(self):
        res = self.sp.read(4)
        #print(res)
        cnt = 0
        start_time = time()
        try:
            while res.decode() != "\n#-\n":
                self.sp.reset_input_buffer() 
                sleep(1)
                #res = self.sp.read(4)
                res=self.sp.read_until(b'\n#-\n',size=4)
                if cnt > self.MAXWAITCNT:
                    print(res.decode())
                    print ("max waiting CNT reached")
                    return -4
                cnt += 1
                if (time()-start_time) > self.MAXWAITTIME:
                    res=self.sp.read_until(b'\n#-\n',size=4)
                    if(res.decode() != "\n#-\n"):
                        return 0
                    print(res.decode())
                    print ("max waiting time reached")
                    return -5
        except UnicodeDecodeError:
            print ("Unicode error, res: " + str(res))
            return 0

        print ("initial seq found " + str(res))
        return 0
    
    def read_event(self):
        print("reading event {}".format(self.evtcnt))
        self.dataframe = []
        if (self.wait_initial_seq()):
            return -1

        # initial sequence found, start reading
        start_time = time()
        #print("start time: " + str(start_time))
        self.dataframe.append("#-\n")
        res = self.sp.readline()
        #print(res.decode(),end=" ")
        if (not res):
            print(res)
            return -2
        while res.decode().split()[0] != "409":
            self.dataframe.append(str(time())  + " " + res.decode())
            res = self.sp.readline()
            if (not res): return -3    
            #print("DT: " + str(time()-start_time))
            if (time()-start_time) > self.MAXREADTIME:
                print ("timeout on finish sequence")
                self.dataframe.append(str(time()) + " " + res.decode())
                self.sp.reset_input_buffer() 
                sleep(0.2)
        
                print("storing event and returning due to timeout")
                self.store_event()
                self.evtcnt += 1

                return -1
            #print("inside " + res.decode(),end=" ")
                
        #print("out while " + res.decode(),end=" ")
        self.dataframe.append(str(time()) + " " + res.decode())
        self.sp.reset_input_buffer() 
        sleep(0.2)
        
        print("storing event {}".format(self.evtcnt))
        self.store_event()
        self.evtcnt += 1
        return 0

    def __del__(self):
        self.sp.close()
        self.outfile.close()

if __name__=="__main__":
    #global rootdir, COM

    dev=VERDAQ8(COM,rootdir)

    for i in range(1):
        dev.read_event()
        
