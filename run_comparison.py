import pandas as pd
import numpy as np

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import importlib.util

# Load lib/occupancy.py directly to avoid importing lib package (which triggers matplotlib import)
module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib", "occupancy.py")
spec = importlib.util.spec_from_file_location("occupancy", module_path)
occupancy_lib = importlib.util.module_from_spec(spec)
sys.modules["occupancy"] = occupancy_lib
spec.loader.exec_module(occupancy_lib)

compute_occupancy = occupancy_lib.compute_occupancy
estimate_rate_occupancy = occupancy_lib.estimate_rate_occupancy

def run_demo():
    print("Loading data...")
    # Load real data
    # Use a smaller chunk if full file is too big for quick demo, but let's try full first
    # Or just read first 1M rows
    data_path = "1_data/df3_valid.csv"
    try:
        df = pd.read_csv(data_path, nrows=1000000) # Read first 1M rows for speed
    except FileNotFoundError:
        print(f"File not found: {data_path}")
        return

    df['time'] = pd.to_datetime(df['time'])
    
    print(f"Loaded {len(df)} samples.")

    # Simple heuristic: Calculate rolling mean of fails to find active regions
    df = df.sort_values('time')
    # fails_inst is 0 or >0. 
    df['rolling_fails'] = df['fails_inst'].rolling(window=1000).mean()

    # Identify a high activity region
    # If max is 0, then no fails in this chunk
    if df['rolling_fails'].max() == 0:
        print("No failures found in the loaded data chunk.")
        return

    high_activity_idx = df['rolling_fails'].idxmax()
    center_time = df.loc[high_activity_idx, 'time']

    # Define segments (e.g. +/- 1 minute around peak)
    high_rate_segment = df[(df['time'] >= center_time - pd.Timedelta(minutes=1)) & 
                           (df['time'] <= center_time + pd.Timedelta(minutes=1))]

    # Low rate: take a quiet period, e.g. start of file if rolling mean is low
    # Or just find min rolling mean
    low_activity_idx = df['rolling_fails'].iloc[1000:].idxmin() # Skip NaN at start
    center_time_low = df.loc[low_activity_idx, 'time']
    low_rate_segment = df[(df['time'] >= center_time_low - pd.Timedelta(minutes=1)) & 
                          (df['time'] <= center_time_low + pd.Timedelta(minutes=1))]

    print(f"High Rate Segment: {len(high_rate_segment)} samples")
    print(f"Low Rate Segment: {len(low_rate_segment)} samples")

    def compare_rates(df_segment, window_size_s):
        occ = compute_occupancy(df_segment, time_col='time', signal_col='fails_inst', window_size_s=window_size_s)
        res = estimate_rate_occupancy(occ, window_size_s=window_size_s)
        return res

    T = 0.1 # 100ms

    res_low = compare_rates(low_rate_segment, T)
    res_high = compare_rates(high_rate_segment, T)

    print("\n--- Low Rate Regime ---")
    print(f"Naive:     {res_low['lambda_naive']:.4f} Hz")
    print(f"Corrected: {res_low['lambda_hat']:.4f} Hz")
    print(f"Occupancy: {res_low['phi']:.2%}")

    print("\n--- High Rate Regime ---")
    print(f"Naive:     {res_high['lambda_naive']:.4f} Hz")
    print(f"Corrected: {res_high['lambda_hat']:.4f} Hz")
    print(f"Occupancy: {res_high['phi']:.2%}")
    
    # Plotting data generation
    windows = np.logspace(-2, 0, 10) # 10ms to 1s
    naive_rates = []
    corrected_rates = []

    print("\n--- Rate vs Window Size (High Rate) ---")
    print("T(s)\tNaive\tCorrected")
    for w in windows:
        r = compare_rates(high_rate_segment, w)
        naive_rates.append(r['lambda_naive'])
        corrected_rates.append(r['lambda_hat'])
        print(f"{w:.3f}\t{r['lambda_naive']:.2f}\t{r['lambda_hat']:.2f}")

if __name__ == "__main__":
    run_demo()
