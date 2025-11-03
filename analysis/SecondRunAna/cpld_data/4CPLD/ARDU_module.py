import serial
import list_ports
from time import sleep

class ARDU:
    idx = 0
    snum = 0
    sp = None
    port = None
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
        print(res)
        if res[0].decode()[:2] == '?>':
            print("ERROR sending to ARDU" + cmd)
            exit()
        return res[0].decode()

    def __init__(self,portn):
        self.port=str(portn)
        try :
            self.sp = serial.Serial(self.port,timeout = 2)
            sleep(2)
        except :
            print("ERROR: port named: " + portn + " connection failed.")
            exit()

        self.idx = ARDU.idx
        ARDU.idx += 1
        #print("TRYING ARDU on port " + str(self.sp.name))
        #res = self.sendQUERY("*IDN?\r")
        #self.snum = int(res.split(", ")[2])
        #print(res)
        #self.snum = int(res)
        #print(self.snum)
        #if self.snum != 1000001:
        #    print("not HERE")
        #    self.sp.close()
        #    return

        print("ARDU " + str(self.idx) + " on port " + str(self.sp.name) + " connected")

    
    def powercycle_V(self):
        print("turning off relay verdaq")
        self.sp = serial.Serial(self.port,timeout = 2)
        self.setOFF_verdaq()
        self.sp.close()
        sleep(60)
        print("turning on relay verdaq")
        self.sp = serial.Serial(self.port,timeout = 2)
        self.setON_verdaq()
        self.sp.close()
        print("waiting 300 s to resume")
        sleep(300)

    def setON_verdaq(self):
        self.sendCMD(":REL1:ON\r")

    def setOFF_verdaq(self):
        self.sendCMD(":REL1:OFF\r")

    def powercycle_C(self):
        print("turning off relay CPLD")
        self.setOFF_cpld()
        self.sp.close()
        print("waiting 300 s to resume")
        sleep(300)
        print("turning off relay CPLD")
        self.sp = serial.Serial(self.port,timeout = 2)
        self.setON_cpld()
        sleep(10)
        self.sp.close()

    def setON_cpld(self):
        self.sendCMD(":REL2:ON\r")

    def setOFF_cpld(self):
        self.sendCMD(":REL2:OFF\r")

    def RST_CPLD(self):
        self.sendCMD(":RST_C:ON\r")
        sleep(1)
        self.sendCMD(":RST_C:OFF\r")
        sleep(1)
    def RST_verdaq(self):
        self.sendCMD(":RST_V:ON\r")
        sleep(1)
        self.sendCMD(":RST_V:OFF\r")
        sleep(1)


    def __del__(self):
        self.sp.close()


if __name__=="__main__":
    ports = list_ports.serial_ports()
    
    dev=ARDU("COM4")
    if dev.snum == 1000001:
        ardu = dev
    #ardu = dev

    ardu.powercycle_C()

        
