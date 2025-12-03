#!/usr/bin/env python
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib
import sys
import matplotlib.dates as mdates
from datetime import datetime, timedelta

#matplotlib.use('Qt5Agg')
#datadir = "." + "/VERDAQ8_data/"
datadir = "dataC"

#fname = datadir +  os.listdir(datadir)[-1]
#fname =  datadir + "/verDAQ8_data_2022_05_24_235910_00011.dat"
fname =  datadir + "/dmm_data6894024_2022_05_25_114444_00000.dat"

fname=""
if len(sys.argv)>1:
    fname = sys.argv[1]
    
print ("ploting file : "+fname)
#dtypes = {'time': 'float32', 'IDC': 'float32', 'IAC': 'float32'}
#df = pd.DataFrame(['time','IDC','IAC'])
dtypes = {0 : 'float64', 1: 'float64', 2: 'float64'}
df = pd.read_csv(fname,delimiter=' ',header=None, dtype=dtypes, parse_dates=[0])

#dfint = df.applymap(lambda x: float(x))

fig, axs = plt.subplots(nrows=2, ncols=1, figsize=(8, 6),sharex=True)
df[0]=df[0].astype('float64').astype('datetime64[s]')#pd.to_datetime(df[0],unit='s')
df[0]=df[0]+timedelta(hours=2)
fig.autofmt_xdate()
#print(df)
df.index = df[0]

df[1].plot(ax=axs[0],ylim=(-0.1,2.0),grid=True)#,layout=(2,4))
df[2].plot(ax=axs[1],ylim=(-3e-5,3e-5),grid=True)#,layout=(2,4))
plt.xlabel="date"
plt.show()

