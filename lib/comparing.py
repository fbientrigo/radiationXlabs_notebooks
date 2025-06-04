import numpy as np
import pandas as pd

def running_diff(df, global_dt):
    timestamps = df['timestamp'].values.astype('datetime64[ns]')
    n = np.arange(len(timestamps))
    t0 = timestamps[0]

    predicted_timestamps = t0 + n * np.timedelta64(int(global_dt * 1e9), 'ns')
    running_dif = (predicted_timestamps - timestamps) / np.timedelta64(1, 's')  # en segundos

    return running_dif