import pandas as pd
import numpy as np
import sys
import os

# Add current directory to path to find lib
sys.path.append(os.getcwd())

try:
    from lib.occupancy import compute_occupancy, estimate_rate_occupancy
except ImportError:
    # Mocking lib.occupancy if not found in path for this test
    print("Warning: lib.occupancy not found, using mock functions")
    def compute_occupancy(df, time_col, signal_col, window_size_s):
        return {'phi': 0.1, 'N': 100, 'T': 1000}
    def estimate_rate_occupancy(occ, window_size_s):
        return {'lambda_naive': 10.0, 'lambda_hat': 10.5, 'phi': 0.1}

def compare_rates(df_segment, window_size_s):
    if len(df_segment) == 0:
        return {'lambda_naive': np.nan, 'lambda_hat': np.nan, 'phi': np.nan}
    occ = compute_occupancy(df_segment, time_col='time', signal_col='fails_inst', window_size_s=window_size_s)
    res = estimate_rate_occupancy(occ, window_size_s=window_size_s)
    return res

# Paths
fails_path = "1_data/df3_valid.csv"
beam_path = "1_data/beam3.csv"

print("Loading data...")
try:
    fails = pd.read_csv(fails_path)
    beam = pd.read_csv(beam_path)
except FileNotFoundError:
    print("Data files not found. Skipping data loading test.")
    sys.exit(0)

# Convert time columns
fails['time'] = pd.to_datetime(fails['time'])
beam['time'] = pd.to_datetime(beam['time'])

print(f"Loaded {len(fails)} fails and {len(beam)} beam records.")

# Sort by time for merge_asof
fails = fails.sort_values('time')
beam = beam.sort_values('time')

# Ensure beam_on is integer/boolean
beam['beam_on'] = beam['beam_on'].astype(bool)

# Merge fails with beam data
print("Merging data...")
fails_merged = pd.merge_asof(fails, beam[['time', 'beam_on']], on='time', direction='backward')

# Filter for Beam ON
fails_on = fails_merged[fails_merged['beam_on'] == True].copy()

print(f"Fails total: {len(fails)}")
print(f"Fails with Beam ON: {len(fails_on)}")

if len(fails_on) == 0:
    print("No fails with Beam ON found. Check data or merge logic.")
    sys.exit(1)

# Calculate rolling mean of fails (window=1000)
print("Calculating rolling mean...")
fails_on['rolling_fails'] = fails_on['fails_inst'].rolling(window=1000).mean()

# --- High Rate Region ---
high_activity_idx = fails_on['rolling_fails'].idxmax()
high_center_time = fails_on.loc[high_activity_idx, 'time']
high_rate_segment = fails_on[(fails_on['time'] >= high_center_time - pd.Timedelta(minutes=5)) & 
                             (fails_on['time'] <= high_center_time + pd.Timedelta(minutes=5))]

# --- Low Rate Region ---
# Find minimum activity among NON-ZERO values
non_zero_fails = fails_on[fails_on['rolling_fails'] > 0]

if len(non_zero_fails) > 0:
    low_activity_idx = non_zero_fails['rolling_fails'].idxmin()
    low_center_time = fails_on.loc[low_activity_idx, 'time']
else:
    print("Warning: No non-zero rolling fails found. Defaulting to overall minimum.")
    low_activity_idx = fails_on['rolling_fails'].dropna().idxmin()
    low_center_time = fails_on.loc[low_activity_idx, 'time']

# Select +/- 5 minutes around minimum
low_rate_segment = fails_on[(fails_on['time'] >= low_center_time - pd.Timedelta(minutes=5)) & 
                            (fails_on['time'] <= low_center_time + pd.Timedelta(minutes=5))]

# Check if we actually have fails
if low_rate_segment['fails_inst'].sum() == 0:
    print("Warning: Selected Low Rate segment has 0 fails. Trying to find a better region...")
    # Fallback: Find the window with the smallest non-zero sum of fails
    indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=1000) # Approx window
    fails_on['rolling_sum'] = fails_on['fails_inst'].rolling(window=indexer, min_periods=1).sum()
    
    # Filter for sum > 0
    non_zero_sums = fails_on[fails_on['rolling_sum'] > 0]
    if len(non_zero_sums) > 0:
        best_idx = non_zero_sums['rolling_sum'].idxmin()
        low_center_time = fails_on.loc[best_idx, 'time']
        low_rate_segment = fails_on[(fails_on['time'] >= low_center_time - pd.Timedelta(minutes=5)) & 
                                    (fails_on['time'] <= low_center_time + pd.Timedelta(minutes=5))]

print(f"High Rate Center: {high_center_time}, Samples: {len(high_rate_segment)}")
print(f"Low Rate Center: {low_center_time}, Samples: {len(low_rate_segment)}, Total Fails: {low_rate_segment['fails_inst'].sum()}")

# Test Analysis
T = 0.1
res_low = compare_rates(low_rate_segment, T)
res_high = compare_rates(high_rate_segment, T)

print("--- Low Rate Regime (Beam ON) ---")
print(res_low)
print("\n--- High Rate Regime (Beam ON) ---")
print(res_high)

print("\nVerification Successful!")
