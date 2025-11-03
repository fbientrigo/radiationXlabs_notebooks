from __future__ import print_function
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import os
import sys
from datetime import datetime, timedelta
from time import sleep, time
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
######
ts = time() 
names = ['ch'+str(x+1) for x in range(8)]
names = ['time','idx'] + names
converters = dict(zip([k+1 for k in range(9)],[HEX2INT]*9))
converters[0]= lambda x: x if '#' not in x else 'nan'
#print(converters)
df = pd.read_csv('../verDAQ8_data_2022_05_25-29_all.dat',delimiter=' ',header=None, names=names, error_bad_lines=False,converters=converters,parse_dates=['time'])
#df = pd.read_csv('../TCMS_RadTest/data_run/VERDAQ8_data/verDAQ8_data_2022_05_25_112617_00000.dat',delimiter=' ',header=None, names=names, error_bad_lines=False,converters=converters,parse_dates=['time'])
df['time'] = df['time'].astype('float64').astype('datetime64[s]') + timedelta(hours=2)
df.insert(1,'time_stmp',float('nan'))
df['time_stmp'] = pd.to_datetime(df['time_stmp'])

te=time()
print("reading total time: {0:3f}s".format(te-ts))

#for k in range(8):
#    df['ch'+str(k+1)] = df['ch'+str(k+1)].astype('float64')
#df['idx'] = df['idx'].astype('float64')


##
ts = time() 
curr_t = pd.to_datetime(float('nan'))
k = 0
total = len(df)
rows = zip(range(total),df['time'],df['ch1'])
tstmp = [curr_t]*total
#for idx, row in df.iterrows():
for (idx, t, ch1) in rows:
#    t = row['time']
#    ch1 = row['ch1']
    if (not pd.isnull(t)) and (pd.isnull(ch1)):
        curr_t = t
        k = 0
#    if (idx<10 and not pd.isnull(t)):
#    df.loc[idx,'time_stmp'] = curr_t + timedelta(milliseconds=5*k)
    tstmp[idx] = curr_t + timedelta(milliseconds=5*k)
    k = k+1
    if (idx%20000)==0 and idx>0:
        te = time()
        etc = (te-ts)*(float(total)/idx - 1)
        print("{0:0.3f} % ETC: {1:0.3f} s \r".format(idx/float(total)*100,etc),end="\r")
        #print("{0:0.3f} %".format(idx/float(total)*100),end='\r')
    
df['time_stmp'] = tstmp
te=time()
print("adding time stmp, total time: {0:3f}s".format(te-ts))


#print(df.head())
#print(df.dtypes)

ts = time() 
t0 = datetime(2022,5,25,8)
DT=12
for k in range(9):
    t1 = t0 + timedelta(hours=DT)
    xlim = (t0,t1)
    suff=str(t0).replace(' ','__').replace(':','_')
    print(suff)
    #df[('2022-05-25 08:00:00'< df['time']) & (df['time']<'2022-05-25 20:00:00')].loc[:,(df.columns!='time')].plot(x='time_stmp',subplots=True,ylim=(-300,4300), xlim=(), figsize=(9,6))
    df[(t0< df['time']) & (df['time']<t1)].loc[:,(df.columns!='time')].plot(x='time_stmp',subplots=True,ylim=(-300,4300), xlim=xlim, figsize=(9,6))
    #plt.show()
    plt.ioff()
    plt.savefig('../FirstRunAna/std_view_'+suff+'.svg', bbox_inches='tight')
    t0 = t0 + timedelta(hours=DT)
te = time() 
print("ploting, total time: {0:3f}s".format(te-ts))
