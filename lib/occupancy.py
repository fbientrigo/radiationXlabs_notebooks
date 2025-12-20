"""
Reset-Latch Occupancy Model Utilities.

This module implements the statistical correction for a Reset-Latch system with fixed time windows.
It addresses the saturation (dead-time) bias inherent in the naïve edge-counting estimator
by using the occupancy fraction phi to estimate the true Poisson rate lambda.

Model:
  - Time is divided into fixed intervals of duration T.
  - For each interval, we observe a binary variable b in {0, 1} (Occupied/Not Occupied).
  - Occupancy fraction phi = N_occupied / N_total.
  - Corrected rate lambda_hat = -(1/T) * ln(1 - phi).
"""

import numpy as np
import pandas as pd
from scipy import stats

def compute_occupancy(
    df: pd.DataFrame,
    time_col: str = "time",
    signal_col: str = "fails_inst",
    window_size_s: float = 1.0,
    start_time: pd.Timestamp = None,
    end_time: pd.Timestamp = None
) -> pd.DataFrame:
    """
    Divide time into fixed windows and determine occupancy for each window.

    A window is considered "occupied" (b=1) if the maximum value of `signal_col`
    within that window is greater than 0. Otherwise b=0.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame containing timestamped data.
    time_col : str
        Name of the timestamp column.
    signal_col : str
        Name of the column indicating fault status (e.g. 'fails_inst', 'total_fails').
        Values > 0 indicate a fault.
    window_size_s : float
        Duration of the fixed time window T in seconds.
    start_time : pd.Timestamp, optional
        Start time for binning. If None, uses min(df[time_col]).
    end_time : pd.Timestamp, optional
        End time for binning. If None, uses max(df[time_col]).

    Returns
    -------
    pd.DataFrame
        DataFrame with one row per window, indexed by window start time.
        Columns:
            - window_end: Timestamp of window end.
            - max_signal: Maximum signal value in the window.
            - is_occupied: 1 if max_signal > 0, else 0.
    """
    if df.empty:
        return pd.DataFrame()

    # Ensure time column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        times = pd.to_datetime(df[time_col])
    else:
        times = df[time_col]

    # Define bin edges
    t_min = start_time if start_time is not None else times.min()
    t_max = end_time if end_time is not None else times.max()
    
    # Create a time index for resampling
    # We copy relevant columns to a new DF to avoid modifying the input
    temp_df = df[[time_col, signal_col]].copy()
    temp_df[time_col] = times
    temp_df = temp_df.set_index(time_col).sort_index()

    # Resample
    # rule=f"{window_size_s}S" might fail if window_size_s is float like 0.1
    # So we use 'L' (milliseconds) or 'U' (microseconds) or 'N' (nanoseconds) if needed,
    # or just convert to integer milliseconds if possible.
    # For robustness with floats, we can use 'S' if it's integer-ish, or 'ms'.
    # Let's use 'N' (nanoseconds) for high precision.
    window_ns = int(window_size_s * 1e9)
    resampler = temp_df.resample(f"{window_ns}ns", origin=t_min)

    # Compute max signal per bin
    # We use max() to see if ANY fault occurred.
    # fillna(0) handles empty bins (assuming no data = no fault, which is a strong assumption 
    # but standard for "continuous" monitoring. If beam was off, user should filter beforehand).
    binned = resampler[signal_col].max().fillna(0)
    
    # If t_max extends beyond the last bin, resample might cut off or extend.
    # We enforce the range if needed, but resample usually covers from start to last data point.
    
    out = pd.DataFrame(index=binned.index)
    out["window_end"] = out.index + pd.Timedelta(seconds=window_size_s)
    out["max_signal"] = binned
    out["is_occupied"] = (binned > 0).astype(int)
    
    return out

def estimate_rate_occupancy(
    occupancy_df: pd.DataFrame,
    window_size_s: float,
    confidence_level: float = 0.95
) -> dict:
    """
    Estimate the corrected Poisson rate lambda from occupancy data.

    Formula: lambda_hat = -(1/T) * ln(1 - phi)
    where phi = N_occupied / N_total.

    Parameters
    ----------
    occupancy_df : pd.DataFrame
        Output from compute_occupancy. Must contain 'is_occupied'.
    window_size_s : float
        Duration of the fixed time window T in seconds.
    confidence_level : float
        Confidence level for the interval (default 0.95).

    Returns
    -------
    dict
        Dictionary containing:
            - N_total: Total number of windows.
            - N_occupied: Number of occupied windows.
            - phi: Occupancy fraction.
            - lambda_hat: Corrected rate estimate (events/s).
            - lambda_naive: Naïve rate estimate (phi / T) (events/s).
            - lambda_lower: Lower bound of CI.
            - lambda_upper: Upper bound of CI.
            - window_size_s: T used.
    """
    if occupancy_df.empty:
        return {
            "N_total": 0, "N_occupied": 0, "phi": 0.0,
            "lambda_hat": 0.0, "lambda_naive": 0.0,
            "lambda_lower": 0.0, "lambda_upper": 0.0,
            "window_size_s": window_size_s
        }

    N_total = len(occupancy_df)
    N_occupied = occupancy_df["is_occupied"].sum()
    phi = N_occupied / N_total

    # Naïve estimator
    lambda_naive = phi / window_size_s

    # Corrected estimator
    # If phi = 1, lambda is infinite (saturation). We handle this gracefully.
    if phi >= 1.0:
        lambda_hat = np.inf
        lambda_lower = np.nan
        lambda_upper = np.inf
    else:
        lambda_hat = -(1.0 / window_size_s) * np.log(1.0 - phi)
        
        # Standard Error for phi (binomial proportion)
        # SE_phi = sqrt(phi * (1 - phi) / N)
        se_phi = np.sqrt(phi * (1.0 - phi) / N_total)
        
        # Standard Error for lambda_hat via Delta Method
        # d(lambda)/d(phi) = 1 / (T * (1 - phi))
        # SE_lambda = |d(lambda)/d(phi)| * SE_phi
        se_lambda = (1.0 / (window_size_s * (1.0 - phi))) * se_phi
        
        # Confidence Interval (Normal approximation)
        z_score = stats.norm.ppf(1 - (1 - confidence_level) / 2)
        lambda_lower = max(0.0, lambda_hat - z_score * se_lambda)
        lambda_upper = lambda_hat + z_score * se_lambda

    return {
        "N_total": N_total,
        "N_occupied": N_occupied,
        "phi": phi,
        "lambda_hat": lambda_hat,
        "lambda_naive": lambda_naive,
        "lambda_lower": lambda_lower,
        "lambda_upper": lambda_upper,
        "window_size_s": window_size_s
    }
