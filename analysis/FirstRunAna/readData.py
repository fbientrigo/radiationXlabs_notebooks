import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib
import sys
from datetime import datetime, timedelta
from time import sleep, time
import numpy as np
from __future__ import print_function

def HEX2INT(value, default = 0):
    if ('.' not in str(value)) and ('#' not in str(value)):
        try:
            return int(value,base=16)
        except (ValueError, TypeError):
            #print("## WARNING: value: "+ str(value) + " was not converted, inserting default")
            pass
    else :
        pass
######
names = ['ch'+str(x+1) for x in range(8)]
names = ['time','idx'] + names
converters = dict(zip([k+1 for k in range(9)],[HEX2INT]*9))
converters[0]= lambda x: x if '#' not in x else 'nan'
#print(converters)
#df = pd.read_csv('verDAQ8_data_2022_05_25-29_all.dat',delimiter=' ',header=None, names=names, error_bad_lines=False,converters=converters,parse_dates=['time'])
df = pd.read_csv('TCMS_RadTest/data_run/VERDAQ8_data/verDAQ8_data_2022_05_25_112617_00000.dat',delimiter=' ',header=None, names=names, error_bad_lines=False,converters=converters,parse_dates=['time'])
df['time'] = df['time'].astype('float64').astype('datetime64[s]') + timedelta(hours=2)
df.insert(1,'time_stmp',float('nan'))
df['time_stmp'] = pd.to_datetime(df['time_stmp'])
