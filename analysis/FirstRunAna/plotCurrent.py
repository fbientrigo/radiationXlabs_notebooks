import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib
import sys
from datetime import datetime, timedelta
from time import sleep, time
import numpy as np
import pandas.plotting._converter as pandacnv
from ROOT import TH1D, TCanvas, TNtuple, kBlue, kRed, kBlack
pandacnv.register()
names = ['time','IDC','IAC']
df = pd.read_csv("../dmm_data_2022_05_25-29.dat",delimiter=' ',header=None, names=names, error_bad_lines=False,parse_dates=['time'])
df['time'] = df['time'].astype('float64').astype('datetime64[s]') + timedelta(hours=2)

ts = time() 
t0 = datetime(2022,5,25,8)
DT=12
for k in range(9):
    try:
        t1 = t0 + timedelta(hours=DT)
        xlim = (t0,t1)
        suff=str(t0).replace(' ','__').replace(':','_')
        print(suff)
        df[(t0< df['time']) & (df['time']<t1)].plot(x='time',y='IDC',grid=True,xlim=xlim, ylim=(0,1.6), figsize=(9,6), marker='.',linestyle='--')
        #plt.show()
        plt.ylabel('IDC A')
        plt.ioff()
        plt.savefig('../FirstRunAna/current_std_view_'+suff+'.svg', bbox_inches='tight')
    except:
        pass
    t0 = t0 + timedelta(hours=DT)
te = time() 
print("ploting, total time: {0:3f}s".format(te-ts))
