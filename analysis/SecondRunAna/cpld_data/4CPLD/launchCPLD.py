#! /usr/bin/env python

## No se ocupan:
#import serial 
#from DMM_module import DMM 
#from verDAQ8_module import VERDAQ #No se ocupa mientras ocupemos CPLD

import errno  # Para importar error FileExistsError al crear directorios para CPLD
import logging
import os
import signal
import sys
from datetime import datetime
from time import sleep
from traceback import print_tb

import pandas as pd

import list_ports
from ARDU_module import ARDU
from CPLD_module import CPLD

CPLD_com = "COM10"
arduino_com = "COM6"
MAXCNTLOW = 2 
MINI = 0.081 # valor previo: 1

## Analogamente,...
MAXCNTHIGH = 2
MAXI = 0.085 # valor previo: 1.5
## Módulo Manager: Routine for radiation tests DAQ.
# IMPORTANTE: Todo el código asociado a la verDAQ8 quedó comentado.




# def signal_handler(sig, frame):
#     print('Going out of verdaq DAQ, au revoir!')
#     sys.exit(0)


######### Manejo de Señal Cierre de Consola Ctrl+C ################
def signal_handler(sig, frame):
    print('Going out of CPDL module, au revoir!')
    # Raise a SystemExit exception, signaling an intention to exit the interpreter.
    sys.exit(0) # argument is giving the exit status; zero is considered “successful termination”

# Si KeyBoardInterrupt, entonces se maneja con fx signal_handler.
signal.signal(signal.SIGINT, signal_handler) 
    # Consider:
    # signal.signal = allows defining custom handlers to be executed when a signal is received
    # (the 'signal') SIGINT = The process was “interrupted”. This happens when you press Control+C on
    # the controlling terminal.

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

###################################################################

###################### Creación directorios #######################

    # obs: subcarpeta cpld se crea en 'main loop cpld' (más abajo)
rootdir = "data_run"
## Run de la CPLD: Carpera que almacena .log y output cpld
try: 
    os.mkdir(rootdir) 
except OSError as e:
    # Si la carpeta ya existe:
    if e.errno != errno.EEXIST: # Manejamos error FileExistsError
        raise

## Run dmm_module.py: Carpera que almacena outputs DMM
try: 
    os.mkdir(rootdir+'/DMM_data/') 
except OSError as e:
    # Si la carpeta ya existe:
    if e.errno != errno.EEXIST: # Manejamos error FileExistsError
        raise

##################################################################

######################## Paths relativos #########################

## verDAQ8
#rootdir = "modified_code/data_run_postCHARM1" # verdaq

## CPLD


## verDAQ8 y/o CPLD
path_almacenamiento = rootdir + "/daqlog" #path relativo archivo
date = datetime.now().strftime("%Y_%m_%d_%H%M%S")
fname = path_almacenamiento + "_" + date + ".log" # path + nombre_archivo + .log

## DMM (lectura)
datadirC = rootdir + "/DMM_data/"

##################################################################

############### Funciones que revisan la corriente ###############

### Setteo Variables: 

## 'MAXCNTLOW': Número de conteos de corriente, dentro de los últimos 5 que son leidos, que debe
# estar sobre el valor 'MINI' para que la función 'ís_current_low' alerte por consola el error
# y llame al método powercycle de la clase ARDU (reiniciar corriente/cpld)


### Funciones: 

    # Obs: Función check_current que hace uso de las dos funciones 
    # anteriores queda en el main loop de la CPLD (más abajo)

def is_current_low():
    global MINI, MAXCNTLOW, datadirC
    # Obtiene path último .dat creado en subcarpeta DMM_module.py
    # Si se agrega otro archivo .dat durante el run, entonces leerá ese.
    fnameC = datadirC + os.listdir(datadirC)[-1] 
    #print(f'is_current_low_fnameC: {fnameC}')   

    #formato en q se almacena info por columna; {n_columna: datatype} 
    dtypes = {0: 'float64', 1: 'float32', 2: 'float32'} # float64/32 number bit representation

    df = pd.read_csv(fnameC, delimiter=' ', header=None, dtype=dtypes, parse_dates=[
                     0], on_bad_lines='skip')  # error_bad_lines=False)
        # parse_dates convierte dato columna 0 a tipo 'datetime64[ns]'
        # ? - por/para qué hacemos eso? no parece q el numero tiene formato de fecha a priori.

    # Se extraen las últimas 'MAXCNTLOW' (int) **filas** del .dat
    dataC = df.tail(MAXCNTLOW) # Return the last n rows; default 5.


    ## De dichas filas se extrae la segunda columna (pos 1). Luego, se extrae 
    # del data frame 'dataC' solo dichas filas, dentro de dataC[1],
    # que cumplan la condición "MINI > dataC[1]".
    cnt = len(dataC[MINI > dataC[1]]) #contamos las filas q cumplieron la condición
    #Obs: '+1.3173E-1' en el .dat se leen como '0.131173'.

    if cnt >= MAXCNTLOW: 
        ## Si al menos 5 conteos de corriente(?) poseen un valor menor a 'MINI'
        # luego la corriente está baja y avisamos con return TRUE.

        # POTENCIAL PROBLEMA (se deja en readme.md; 03/08):
        # Notar que estamos solo leyendo los últimos 5 conteos de corriente en
        # total de cada archivo output dmm que vamos leyendo. Esto es, podrían 
        # haber bajas de corriente reportadas en el resto del archivo y este 
        # código no lo reportaría.
        return True
    return False


def is_current_high():
    global MAXI, MAXCNTHIGH, datadirC
    fnameC = datadirC + os.listdir(datadirC)[-1]
    dtypes = {0: 'float64', 1: 'float32', 2: 'float32'}
    df = pd.read_csv(fnameC, delimiter=' ', header=None, dtype=dtypes, parse_dates=[
                     0], on_bad_lines='skip')  # error_bad_lines=False)
    dataC = df.tail(MAXCNTHIGH)
    cnt = len(dataC[dataC[1] > MAXI])
    if cnt >= MAXCNTHIGH:
        return True
    return False



##################################################################



######################## Setteo de Logging #######################

# Logging is a means of tracking events that happen when some software runs. 
    ## Se define el logging para este módulo. 
    # Este se puede entregar a clases para que hagan uso de el.

## Setteo formato de como se guardará cada linea dentro archivo .log
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename=fname,
                    filemode='w',
                    level=logging.DEBUG)

# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logFormatter = logging.Formatter('%(asctime)s %(message)s')
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
logging.getLogger().addHandler(consoleHandler)

log = logging.getLogger("launchDAQ")
#print(f'log de launch DAQ: {log}')

##################################################################




########## Resto del código: 


################ MAIN LOOP ################

log.info("######### Starting CPLD for the Radiation Test at CHARM #########")

ports = list_ports.serial_ports()
log.info("available ports: ")
for p in ports:
    log.info(p)
    #print(f'avaliable ports: {p}')

### Arduino 
arduino = ARDU(arduino_com)

### CONNECTING DEVICES ####
log.info("connecting devices...")
arduino.setON_cpld()
#Esto para dar tiempo a que se almacenen los datos de corriente.
sleep(8)
del arduino
ports = list_ports.serial_ports()
#print(f'list_ports: {ports}')


###########################################
############## CPLD MAIN LOOP #############
###########################################


## Se crea subcarpeta que almacena outputs cpld
try: 
    os.mkdir(rootdir+'data_run_CPLD') 
except OSError as e:
    # Si la carpeta ya existe:
    if e.errno != errno.EEXIST: # Manejamos error FileExistsError
        raise

## Instanciamos a la cpld, quien hereda el log de este módulo .py
cpld = CPLD(CPLD_com, rootdir, log=log)

# if (arduino and verdaq):
if (cpld):
    log.info("cpld online.") #antes decía 'only'. No era descriptivo de la situación.
    
else:
    log.info("ERROR: device missing")


def check_current():
    '''checkea corriente de la cpld reportada por el digital multimeter
    (DMM_module.py) a través de archivos .dat en subcarpeta DMM_data'''
    global cpld, arduino, log
    #print('ESTOY EN CHECK CURRENT!')
    try:
        if is_current_low(): #retorna TRUE or FALSE 
            log.error("cpld current low, sending power cycle")
            arduino = ARDU(arduino_com)
            arduino.powercycle_C() # se apaga y enciende la fuente de corriente.
            del cpld
            del arduino
            cpld = CPLD(CPLD_com, rootdir, log=log)
            return True
        if is_current_high(): #retorna TRUE or FALSE 
            log.error("cpld current high, sending power cycle")
            arduino = ARDU(arduino_com)
            arduino.powercycle_C() # se apaga y enciende la fuente de corriente.
            del cpld
            del arduino
            cpld = CPLD(CPLD_com, rootdir, log=log)
            return True
    except:
        print("Error reading current file. skipping")

    return False

count_err = 0
# for k in range(5):
while (True):
    if (check_current()): # retorna True si hay problemas con corriente que recibe CPLD.
        continue # No se corre código de abajo y se pasa a la siguente iteración.   
    try:
        ret = cpld.read_event()
        print(ret)
        #sleep(0.1)
        if (ret): # ssi ret!= 0 se entra al if. Si es 0, eventó se leyó bien.
            log.error("cpld not responding, sending power cycle, error_code:"+str(ret))
            arduino = ARDU(arduino_com)
            arduino.powercycle_C()
            del cpld
            del arduino
            cpld = CPLD(CPLD_com, rootdir, log=log)
            continue
        log.info("event stored")
    except:
        print("Error en read event")
        count_err+=1
        sleep(1)
        if (count_err > 4):
            count_err = 0
            arduino= ARDU(arduino_com)
            arduino.powercycle_C()
            del arduino
