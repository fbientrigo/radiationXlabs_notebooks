"""
Test script for Reset-Latch Occupancy Model.
"""

import sys
import os
import importlib.util
import numpy as np
import pandas as pd

# Load lib/occupancy.py directly to avoid importing lib package (which triggers matplotlib import)
module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "occupancy.py")
spec = importlib.util.spec_from_file_location("occupancy", module_path)
occupancy_lib = importlib.util.module_from_spec(spec)
sys.modules["occupancy"] = occupancy_lib
spec.loader.exec_module(occupancy_lib)

compute_occupancy = occupancy_lib.compute_occupancy
estimate_rate_occupancy = occupancy_lib.estimate_rate_occupancy

def simulate_latch_data(
    true_rate: float,
    duration_s: float,
    window_size_s: float,
    dead_time_s: float = 0.0
) -> pd.DataFrame:
    """
    Simulate Poisson events and a latch response.
    """
    # 1. Generate Poisson event times
    n_events = int(true_rate * duration_s)
    if n_events == 0:
        return pd.DataFrame(columns=["time", "fails_inst"])
        
    inter_arrivals = np.random.exponential(1.0 / true_rate, size=int(n_events * 1.2))
    event_times = np.cumsum(inter_arrivals)
    event_times = event_times[event_times <= duration_s]
    
    # 2. Create a sampled DataFrame (e.g. 100Hz sampling)
    sampling_rate_hz = 100.0
    n_samples = int(duration_s * sampling_rate_hz)
    t_index = np.linspace(0, duration_s, n_samples)
    
    fails_inst = np.zeros(n_samples, dtype=int)
    
    event_indices = np.searchsorted(t_index, event_times)
    event_indices = event_indices[event_indices < n_samples]
    
    fails_inst[event_indices] = 1
    
    df = pd.DataFrame({
        "time": pd.to_datetime(t_index, unit="s", origin=pd.Timestamp("2024-01-01")),
        "fails_inst": fails_inst
    })
    
    return df

def test_low_rate_regime():
    """
    Case 1: Low Rate (lambda * T << 1).
    Expect lambda_hat approx lambda_naive approx true_rate.
    """
    true_rate = 1.0  # 1 event/s
    window_size_s = 0.01 # T = 10ms -> lambda*T = 0.01 (Low)
    duration_s = 1000.0 # Enough stats
    
    print(f"\n--- Test Low Rate: lambda={true_rate}, T={window_size_s} (lambda*T={true_rate*window_size_s}) ---")
    
    df = simulate_latch_data(true_rate, duration_s, window_size_s)
    
    occ = compute_occupancy(df, window_size_s=window_size_s)
    res = estimate_rate_occupancy(occ, window_size_s)
    
    print(f"Phi: {res['phi']:.4f}")
    print(f"Lambda Naive: {res['lambda_naive']:.4f}")
    print(f"Lambda Hat:   {res['lambda_hat']:.4f}")
    print(f"True Rate:    {true_rate:.4f}")
    
    # Check agreement within 10% (stochastic)
    assert abs(res['lambda_hat'] - true_rate) < 0.1 * true_rate
    assert abs(res['lambda_naive'] - true_rate) < 0.1 * true_rate

def test_high_rate_regime():
    """
    Case 2: High Rate (lambda * T ~ 1).
    Expect lambda_hat approx true_rate.
    Expect lambda_naive < true_rate (saturation).
    """
    true_rate = 100.0 # 100 events/s
    window_size_s = 0.01 # T = 10ms -> lambda*T = 1.0 (High)
    duration_s = 1000.0
    
    print(f"\n--- Test High Rate: lambda={true_rate}, T={window_size_s} (lambda*T={true_rate*window_size_s}) ---")
    
    df = simulate_latch_data(true_rate, duration_s, window_size_s)
    
    occ = compute_occupancy(df, window_size_s=window_size_s)
    res = estimate_rate_occupancy(occ, window_size_s)
    
    print(f"Phi: {res['phi']:.4f}")
    print(f"Lambda Naive: {res['lambda_naive']:.4f}")
    print(f"Lambda Hat:   {res['lambda_hat']:.4f}")
    print(f"True Rate:    {true_rate:.4f}")
    
    # Check lambda_hat is close to true rate
    assert abs(res['lambda_hat'] - true_rate) < 0.1 * true_rate
    
    # Check naive estimator underestimates significantly
    assert res['lambda_naive'] < 0.8 * true_rate
    print("Confirmed: Naive estimator underestimates due to saturation.")

if __name__ == "__main__":
    try:
        test_low_rate_regime()
        test_high_rate_regime()
        print("\nALL TESTS PASSED.")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        exit(1)
