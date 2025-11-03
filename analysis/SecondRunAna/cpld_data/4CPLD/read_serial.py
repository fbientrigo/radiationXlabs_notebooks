

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
res = sp.readline()
#print(res)
start_time = time()
print(res.decode()[-2:])
        #self.dataframe.append("#-\n") #obs: no agregamos salto de línea al inicio
try:
    while res.decode()[0] != "#": #secuencia inicial (válida) esperada

        #### Como no encontramos el msje inicial, seguimos buscando ####
        # Vaciamos el buffer de entrada.
        #self.sp.flushInput() # actualización v3.0; antes 'reset_input_buffer' 
        #sleep(0.2) # para qué?
        res = sp.readline() # leemos otra secuencia de 1 bytes 
        ################################################################
        print(res.decode[-2:])
        # Dejamos de leer bajo dos casos: 
            # ? - Me parece un poco redundante tener dos formas de validar esto
            # orlando me dijo q el primero tenía una razón de ser pero      
            # q no se acordaba. P. volver a preguntar.
        
        #1 leeimos muchos mensajes y jamás llegó el msje esperado
        if cnt > 15:
            print("max waiting CNT reached") 
            #print("max waiting CNT reached") 
            #return -4
        cnt += 1

        #2 Hemos esperado más de la cota_máx definida:
        if (time()-start_time) > 40:
            print("max waiting time reached") 
            #print ("max waiting time reached")
            #return -5

except UnicodeDecodeError: #  illegal sequence of str tried to be decodifed.
    print ("Unicode error, res: " + str(res))
    #return -10
