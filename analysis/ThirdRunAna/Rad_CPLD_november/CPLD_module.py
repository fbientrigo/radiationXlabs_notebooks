

## Módulo que se hará cargo de settear (tunnear) todo lo necesario para el 
# funcionamiento de la CPLD board y que se comunique con `launchDAQ.py` 
# tal que todos los errores provenientes de este módulo sean manejados 
# con dicho modulo manager.

import signal
import sys
import os
import serial
from datetime import datetime
from time import time, sleep
import logging



######### Manejo de Señal Cierre de Consola Ctrl+C ################

## Esto me permite cerrar el módulo a voluntad con Ctrl+C de manera controlada
# (i.e. cuando yo quiera)

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

###################################################################


class CPLD:
    '''In charge of tunning CPLD board in orden to get a proper conection with
    the port. Every possible error that appears here should be managed on the 
    manager's MODULE called launchDAQ.py'''


    ## Parámetros para establecer la conexion serial: 
    sp = None #almacena el objeto 'serial.Serial' que abre el puerto en constructor

        # A través de este objeto podemos intercambiar info con sus métodos:
            # .write(Data to send); return INT = Number of bytes written
            # .read(Number of bytes to read); return Bytes = read from the port.
            # .readline(): reads up to one line, including the \n at the end

    rootdir = 'data_dryrun' #si no existe, directorio se crea en el constructor.
    BAUDRATE = 115200
    TIMEOUT = 2 #P. buscar u.de medida + q implica
    cnt_error = 0

    ## Parámetros para guardar el output del archivo
    fname = "/cpld_data"  # file name, primero va la subcarpeta y
                                    # luego el primer trazo del nombre del archivo
                                    # '.log' que se va a guardar.
    fidx  = 0 #id de los archivos
    outfile = None #P/? aún no entiendo q representa bn este. si un archivo, pero
        	       # de qué.
    MAXFSIZE = 1 #máximo tamaño archivos a guardar (en megabytes)
    dataframe = []  # buffer que guarda el evento en read_evento
                    # tambien se ocupa en replace_ofile


    ## Parámetros de lectura de datos (recibidos)
    MAXWAITCNT = 30   # esperamos leer hasta 15 veces 4bytes (ver método wait_initial_seq)
    MAXREADTIME = 100
    MAXWAITTIME = 40
    evtcnt = 0       # conteo de ventos en método read_event

    ## Otros parámetros
    idx = 0 #id clpd; usado en el constructor.


    def __init__(self,portn,rootdir=None, log = None):
        self.log = log
        self.cnt_error = 0
        ## Establecer conexion con el puerto. 
        # P. Ojalá núm puerto no sea un valor sea hardcodeado en launchDAQ.py
        try :
            self.sp = serial.Serial(str(portn), baudrate=self.BAUDRATE, timeout = self.TIMEOUT)
        except :
            log.info("ERROR: port named: " + portn + " connection failed.")
            #print("ERROR: port named: " + portn + " connection failed.")
            exit()


        ## Si al instanciar la clase le entregamos efectivamente un rootdir,
        # entonces construimos un nombre para el archivo CPLD que se va a guardar.
        if (rootdir != None):
            #returns a string representing date and time
            date = datetime.now().strftime("%Y_%m_%d_%H%M%S")            
            self.rootdir = rootdir
            self.fname = self.rootdir + self.fname
            self.fname += "_" + date + "_" + "{:05d}.dat".format(self.fidx)
            
            try:
                self.outfile = open(self.fname,"w") # crea y escribe sobre el archivo
            except :
                log.info("ERROR: file:"+self.fname+" for CPLD data was not created")
                # print("ERROR: file:"+self.fname+" for CPLD data was not created")
                # ? aún no me queda claro CUANDO y dnd se crea este archivo.
                # más allá del tipo de archivo que será.
                exit()

        log.info("CPLD " + str(self.idx) + " on port " + str(self.sp.name) + " connected")
        #print("CPLD " + str(self.idx) + " on port " + str(self.sp.name) + " connected")
        self.sp.reset_input_buffer() #version actulizada es .flushInput()

    

    ## Dos métodos para la comunicación:
    def sendCMD(self,cmd):
        self.log.info(f'cmd de sendCMD en CPLD: {cmd}')
        #print(f'cmd de sendCMD en CPLD: {cmd}')
        self.sp.write(cmd.encode()) # método write (q envia) de serial.Serial.
        res = self.sp.readline() # respuesta q recibe.

        # P. intentar averiguar el motivo de esto:
        # programa en algún momento pide "enter" para continuar
        # la teoria es q ello ocurre cdo previamente se pasó a mandar un click
        # se tiene la idea de q tmbn tiene q ver con cmo fxna la consola de windows 
        # (y de q quizá ir imprimiendo lo q va ocurriendo en la consola no es
        # tan wena idea x lo mismo)

        if res.decode()[:2] != '=>':
            self.log.info("ERROR sending " + cmd)
            print("ERROR sending " + cmd)
            exit()
        return res.decode()


    def sendQUERY(self,cmd): # ? pq nos queremos conectar con ARDU? 
        print("sending query to ARDU: " + cmd)
        self.sp.write(cmd.encode())  
        res = self.sp.readline(), self.sp.readline()
        if res[0].decode()[:2] == '?>':
            print("ERROR sending to ARDU" + cmd)
            exit()
        return res[0].decode()



    ## Sobre el manejo de los eventos que recibe: 
    def store_event(self):  #GUARDAR EVENTO Q SE RECIBE. 
        ## Limita largo del evento q recibe
            #getsize = retorna tamaño archivo en bytes
        #print(os.path.getsize(self.fname)/50000.)
        if os.path.getsize(self.fname)/10000. > self.MAXFSIZE:
                # obs: se pasan bytes a megabytes para comparar con MAXFSIZE
                # ? - pq el punto al final del número?

            #Si alcanza máximo tamaño 'MAXFSIZE', hago un nuevo archivo.
            self.replace_ofile() # Esto, ocupando un método hecho más abajo.
        for line in self.dataframe:
            self.outfile.write(line)

    def replace_ofile(self): # CREA UN NUEVO ARCHIVO PARA UN MISMO EVENTO CON DIFERENTE ID
        self.fidx +=1 #id de los files para diferenciarlos entre si ??
                    # ? - estos archivos consecutivos parece q son wardados
                    #  con la misma fecha/timepo?
        self.fname = self.fname[:len(self.fname)-9] + "{:05d}.dat".format(self.fidx)
        try:
            print("crendo nuevo archivo")
            self.outfile.close()
            self.outfile = open(self.fname,"w")
        except :
            print("ERROR: file:"+self.fname+" for CPLD data was not created")
            exit()

        for line in self.dataframe: # para q usa el dataframe?? (atributo de clase)
                                    # parece ser cmo el buffer q me comentaba q había.
            self.outfile.write(line)   


    def wait_initial_seq(self):
        '''Implementa dos formas de esperar la llegada de la primera señal desde
        la CPLD. La primera, conteo de lecturas mensajes (MAXWAINTCNT) hasta la 
        llegada del mensaje de opertura esperado. La segunda, cota máx de tiempo a 
        esperar (MAXWAITTIME)'''

        # Leer secuencia que se espera tarjeta envie al inicio (en bytes)
        res = self.sp.readline()
        res = self.sp.readline()

        cnt = 0 #variable aux para el conteo de bytes leidos más abajo 
        start_time = time()
        print(res.decode())
        try:
            while res.decode()[0] != "#": #secuencia inicial (válida) esperada

                #### Como no encontramos el msje inicial, seguimos buscando ####
                # Vaciamos el buffer de entrada.
                #self.sp.flushInput() # actualización v3.0; antes 'reset_input_buffer' 
                #sleep(0.2) # para qué?
                res = self.sp.readline() # leemos otra secuencia de 1 bytes 
                ################################################################
                print(res.decode())
                # Dejamos de leer bajo dos casos: 
                    # ? - Me parece un poco redundante tener dos formas de validar esto
                    # orlando me dijo q el primero tenía una razón de ser pero      
                    # q no se acordaba. P. volver a preguntar.
                
                #1 leeimos muchos mensajes y jamás llegó el msje esperado
                if cnt > self.MAXWAITCNT:
                    self.log.error("max waiting CNT reached") 
                    #print("max waiting CNT reached") 
                    return -4
                cnt += 1

                #2 Hemos esperado más de la cota_máx definida:
                if (time()-start_time) > self.MAXWAITTIME:
                    self.log.error("max waiting time reached") 
                    #print ("max waiting time reached")
                    return -5

        except UnicodeDecodeError: #  illegal sequence of str tried to be decodifed.
            print ("Unicode error, res: " + str(res))
            return -10
        sleep(0.2)
        #print ("initial seq found " + str(res))
        return 0 # si no hay error; Si se retorna otro número, es pq hubo un error 
        

    def read_event2(self): #puedo copiarlo
        self.log.info("reading event {}".format(self.evtcnt))
        #print("reading event {}".format(self.evtcnt))
        self.dataframe = [] #buffer que almacena (en ram) el msje recibido
        
        #if (self.wait_initial_seq()): # ssi != 0.
            # Que es de hecho el único caso cuando no hay error en wait_initial_seq
        #    return -1

        # Por lo anterior, si llega acá entonces:
        # initial sequence found, start reading
        start_time = time()
        #self.dataframe.append("#-\n") #obs: no agregamos salto de línea al inicio
        res = self.sp.readline() # leemos una linea (en bytes);
            # (readline lee hasta el siguiente salto de línea)
            # Se quita salto de línea entre msje inicial '#' 
            # y lo sgte para que el .readline() lea efectivamente 
            # lo que sigue al msje inicia y no solo '\n'
        cnt = 0
        while(res.decode()[0]!='#'):
            cnt+=1
            res = self.sp.readline()
            if(cnt > self.MAXWAITCNT):
                print("Max cnt reach")
                return -1
        #print(f'res_readline en read_event {res}')
        print(res.decode())
        
        if (not res): #ssi res!= None ó '' (texto vacio)
            return -2
        #end sequence
        #print(res.decode()[-2]+res.decode()[-1])
        # Leemos mensaje hasta llegar a la secuencia final
        while (res.decode()[-2]+res.decode()[-1]) != "*\n": 
            
            self.dataframe.append(str(time())  + " " + res.decode())
            #? - pq no llamamos al método reset buffet de serial y .store_event()
            #res = self.sp.readline() #leemos una nueva linea supongo ?, tiene memmoria c/r a lo q leyó antes??
            #print(time()-start_time)
            if (not res): return -3    
        
            #print("DT: " + str(time()-start_time))

            #repetimos la idea del método wait_initial_seq para las siguientes líneas
            if (time()-start_time) > self.MAXREADTIME:
                self.log.info("timeout on finish sequence")
                #print("timeout on finish sequence")
                self.dataframe.append(str(time()) + " " + res.decode())
                self.sp.reset_input_buffer() #.flushInput() es la version actualizada
                sleep(0.2)
        
                self.log.info("storing event and returning due to timeout")
                #print("storing event and returning due to timeout")
                self.store_event()
                self.evtcnt += 1

                return -1
            #print("inside " + res.decode(),end=" ")
                
        #print("out while " + res.decode(),end=" ")
        self.dataframe.append(str(time()) + " " + res.decode())
        self.sp.reset_input_buffer() 
        sleep(0.2)
        
        self.log.info("storing event {}".format(self.evtcnt))
        #print("storing event {}".format(self.evtcnt))
        self.store_event()
        self.evtcnt += 1
        return 0
    def read_event(self): #puedo copiarlo
        self.log.info("reading event {}".format(self.evtcnt))
        #print("reading event {}".format(self.evtcnt))
        self.dataframe = [] #buffer que almacena (en ram) el msje recibido
        
        start_time = time()
        res = self.sp.read(14) 
        cnt = 0
        if(self.cnt_error > 400):
            self.cnt_error = 0
            print('Error count:'+str(self.cnt_error))
            print('Many errors detected')
            self.dataframe.append(str(time()) + "," + 'reset'+"\n")
            self.sp.reset_input_buffer() 
            sleep(0.4)
            self.log.info("storing event {}".format(self.evtcnt))
            #print("storing event {}".format(self.evtcnt))
            self.store_event()
            self.evtcnt += 1
            return -1
            
        for j in range (0,20):
            for i in range(0,20):
                res = self.sp.read(1)
                if(res.decode() == '\n'):
                    res = self.sp.read(14)
                    break
            if((res.decode()[0]=='#') and (res.decode()[-2:]=='*\n')):
                break
            else:
                print('Error count:'+str(self.cnt_error))
                self.cnt_error+=1     
            if(j==20):
                print("Max cnt reach")
                return -2
        
        #for i in range (0,20):
        #    res = self.sp.readline()
        #    if((res.decode()[0]=='#') and (res.decode()[-2:]=='*\n')):
        #        break
        #    else:
        #        print('Error count:'+str(self.cnt_error))
        #        self.cnt_error+=1     
        #    if(i==20):
        #        print("Max cnt reach")
        #        return -2
        #while(res.decode()[0]!='#'):
        #    cnt+=1
        #    res = self.sp.readline()
        #    if(cnt > self.MAXWAITCNT):
        #        print("Max cnt reach")
        #        return -1
        #print(f'res_readline en read_event {res}')
        print(res.decode())
        cnt_ones = 0
        cnt_F = 0
             
        if(res.decode()[3]=='F'):
            cnt_F+=1
        if(res.decode()[4]=='F'):
            cnt_F+=1
        if(res.decode()[8]=='F'):
            cnt_F+=1
        if(res.decode()[9]=='F'):
            cnt_F+=1
        
        if((cnt_F < 3)):
            self.cnt_error+=1
            print('Error count:'+str(self.cnt_error))
        else:
            #No hay tantos errores seguidos
            if(self.cnt_error < 100):
                self.cnt_error = 0

        

        if (not res): #ssi res!= None ó '' (texto vacio)
            return -2

        if (res.decode()[-2:] == '*\n'):
            self.dataframe.append(str(time()) + "," + res.decode()[1:-2]+"\n")
            self.sp.reset_input_buffer() 
            sleep(0.4)
            self.log.info("storing event {}".format(self.evtcnt))
            #print("storing event {}".format(self.evtcnt))
            self.store_event()
            self.evtcnt += 1
            return 0
        print("Not finish seq")
        self.cnt_error+=1
        sleep(0.4)
        return 0
       
        

    def __del__(self):
        self.sp.close() #cerramos el puerto
        self.outfile.close() #?
    

    # Pretendemos recibir información
    #  P. aún no deciden el tipo de dato de clase
    # ; clase no se podrá terminar hasta q eso pase

if __name__ == '__main__':

    ######### Logging propio del módulo #########

    # Logging is a means of tracking events that happen when some software runs. 
        ## Se define el logging para este módulo. 
        # Este se puede entregar a clases para que hagan uso de el.

    rootdir = "data_test_CPLD" #28/07 testeo cpld
    fname = rootdir + "/cpldmodulelog" #para denotar que es un log propio
    date = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        #19/07 nombre .log #esto es fname pero incluye dnd se guardará el archivo también
    fname = fname + "_" + date + ".log" 

    # ? - en q momento acá se crea el .log llamado "/cpldmodulelog"

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

    log_cpld = logging.getLogger("CPLD_module") #instanciación logging.

    cpld=CPLD("COM10", rootdir, log = log_cpld)
    efr=cpld.read_event()
    print(efr)
    efr=cpld.read_event()
    print(efr)

    efr=cpld.read_event()
    print(efr)

    ##############################################
    