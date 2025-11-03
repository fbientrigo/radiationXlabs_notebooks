import pandas as pd
import matplotlib.pyplot as plt
import os

datadir = "data_debug" + "/VERDAQ8_data/"

fname = datadir +  os.listdir(datadir)[-1]
#fname =  datadir + "/verDAQ8_data_2022_05_23_155346_00000.dat"
print ("ploting file : "+fname)

df = pd.read_table(fname,delimiter=' ',skiprows=2, header=None)
#dfint = df.applymap(int,base=16)
df = df[df[0].apply(lambda x : "#" not in str(x))]
dfint = df[df[1].apply(lambda x : "#" not in x)].loc[:,df.columns!=0].applymap(int,base=16)
#print(dfint)

#dfint[(30 < dfint[0] ) & (dfint[0]<1040)].loc[:,df.columns!=0].plot(subplots=True)#,layout=(2,4))

dfint.plot(subplots=True)#,layout=(2,4))
plt.show()

