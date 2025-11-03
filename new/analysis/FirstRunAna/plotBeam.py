import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib
import sys
from datetime import datetime, timedelta
from time import sleep, time
import numpy as np

ts = time() 

df0 = pd.read_csv("../user_data_slot9_0525-3125/Orlando_Soto_-_Slot_9/RUN_8_USER_/data_CHARMB_7.csv")
df1 = pd.read_csv("../user_data/USER_Orlando_Soto_-_Slot_10-11/RUN_9_USER_/data_CHARMB_7.csv")
df2 = pd.read_csv("../user_data/USER_Orlando_Soto_-_Slot_10-11/RUN_10_USER_/data_CHARMB_7.csv")
df3 = pd.read_csv("../user_data/USER_Orlando_Soto_-_Slot_10-11/RUN_10_USER_/data_CHARMB_7_2.csv")

vname = 'TID_RAW1' 
df1[vname] = df1[vname].apply(lambda x: x + df0.iloc[-1][vname])
df2[vname] = df2[vname].apply(lambda x: x + df1.iloc[-1][vname])
df3[vname] = df3[vname].apply(lambda x: x + df2.iloc[-1][vname])

vname = 'HEH' 
df1[vname] = df1[vname].apply(lambda x: x + df0.iloc[-1][vname])
df2[vname] = df2[vname].apply(lambda x: x + df1.iloc[-1][vname])
df3[vname] = df3[vname].apply(lambda x: x + df2.iloc[-1][vname])

vname = 'N1MeV_RAW0' 
df1[vname] = df1[vname].apply(lambda x: x + df0.iloc[-1][vname])
df2[vname] = df2[vname].apply(lambda x: x + df1.iloc[-1][vname])
df3[vname] = df3[vname].apply(lambda x: x + df2.iloc[-1][vname])

df = pd.concat([df0,df1,df2,df3], axis=0)
df['Time'] = df['Time'].astype('datetime64[ns]')
df.index = df['Time'] 
df = df.rename(columns={'TID_RAW1':'TID','N1MeV_RAW0':'N1MeV'})
te = time() 
print("reading, total time: {0:3f}s".format(te-ts))

ts = time() 
t0 = datetime(2022,5,25,8)
DT=12
for k in range(9):
    t1 = t0 + timedelta(hours=DT)
    xlim = (t0,t1)
    suff=str(t0).replace(' ','__').replace(':','_')
    print(suff)
    #df[('2022-05-25 08:00:00'< df['time']) & (df['time']<'2022-05-25 20:00:00')].loc[:,(df.columns!='time')].plot(x='time_stmp',subplots=True,ylim=(-300,4300), xlim=(), figsize=(9,6))
    df[(t0< df['Time']) & (df['Time']<t1)].loc[:,(df.columns=='TID')].plot(grid=True,xlim=xlim, figsize=(9,6))
    #plt.show()
    plt.ioff()
    plt.savefig('../FirstRunAna/beam_std_view_'+suff+'.svg', bbox_inches='tight')
    t0 = t0 + timedelta(hours=DT)
te = time() 
print("ploting, total time: {0:3f}s".format(te-ts))
