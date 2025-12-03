#!/usr/bin/env python
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib
import sys
from datetime import datetime, timedelta
import numpy as np

def HEX2INT(value, default = 0):
    if ('.' not in str(value)) and ('#' not in str(value)):
        try:
            return int(value,base=16)
        except (ValueError, TypeError):
            #print("## WARNING: value: "+ str(value) + " was not converted, inserting default")
            pass
    else :
        pass

    
VDAQ_DTYPES = dict(zip([k for k in range(10)],['str']*10))
names = [x for x in range(10)]
converters = dict(zip([k+1 for k in range(9)],[HEX2INT]*9))
converters[0]= lambda x: x if '#' not in x else 'nan'
print(converters)
#df = pd.read_csv('TCMS_RadTest/data_run/VERDAQ8_data/verDAQ8_data_2022_05_29_082200_00001.dat',delimiter=' ',header=None, names=names, dtype=VDAQ_DTYPES, error_bad_lines=False)
df = pd.read_csv('verDAQ8_data_2022_05_25-29_all.dat',delimiter=' ',header=None, names=names, error_bad_lines=False,converters=converters,parse_dates=[0])

#df = df[df[0].apply(lambda x : "#" not in str(x))]
#df = df[df[1].apply(lambda x : "#" not in str(x))]
df[0] = df[0].astype('float64').astype('datetime64[s]') + timedelta(hours=2)


