
# poisson_binning.py
# Reset-aware Poisson binning and trend analysis for radiation reliability experiments.
#
# Usage example (expects df_beam, df_fails dataframes with 'time' columns):
#   from poisson_binning import (
#       detect_resets, extract_events, build_bins_by_resets, bin_and_rate,
#       poisson_rate_mle, garwood_ci_rate, fit_poisson_trend
#   )
#   bins2 = bin_and_rate(df_beam2, fails_run2, n_subsystems=32, flux_col='N1MeV_dose_rate')
#   bins3 = bin_and_rate(df_beam3, fails_run3, n_subsystems=16, flux_col='N1MeV_dose_rate')
#   trend = fit_poisson_trend(bins2, use_eq_time=True)
#
# Assumptions:
# - df_beam has columns: 'time' (float seconds or pandas datetime64[ns]),
#   'beam_on' (0/1), optionally 'dt' (seconds), and flux dose-rate column (e.g., 'N1MeV_dose_rate').
# - df_fails has columns: 'time' and 'failsP_acum' (monotonic until resets).

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

import numpy as np
import pandas as pd
from scipy.stats import chi2
from scipy.optimize import minimize

# -----------------------------
# Utilities
# -----------------------------

def _ensure_time_seconds(s: pd.Series) -> np.ndarray:
    """Return time as float seconds (monotonic assumed)."""
    if np.issubdtype(s.dtype, np.number):
        t = s.to_numpy(dtype=float, copy=False)
    else:
        # pandas datetime -> seconds
        t = s.astype('datetime64[ns]').astype('int64') * 1e-9
        t = t.to_numpy(dtype=float, copy=False)
    return t

def _ensure_dt(df: pd.DataFrame) -> np.ndarray:
    """Ensure there is a dt column (seconds) computed from 'time' if missing."""
    if 'dt' in df.columns:
        dt = df['dt'].to_numpy(dtype=float, copy=False)
        # If dt has NaNs or non-positive, recompute safely
        if not np.isfinite(dt).all() or (dt <= 0).all():
            t = _ensure_time_seconds(df['time'])
            dt = np.diff(t, prepend=t[0])
            dt[dt <= 0] = np.nan
    else:
        t = _ensure_time_seconds(df['time'])
        dt = np.diff(t, prepend=t[0])
        dt[dt <= 0] = np.nan
    return dt

# -----------------------------
# Reset detection & event extraction
# -----------------------------

def detect_resets(df_fails: pd.DataFrame, value_col: str = 'failsP_acum') -> pd.DataFrame:
    """
    Detect resets as points where the cumulative counter drops (diff < 0) or is zero
    after being positive. Returns a dataframe with columns ['time', 'kind'] where
    kind in {'start','reset','end'}.
    """
    df = df_fails[['time', value_col]].copy().sort_values('time')
    t = _ensure_time_seconds(df['time'])
    v = df[value_col].to_numpy(dtype=float, copy=False)

    dv = np.diff(v, prepend=v[0])
    # potential resets: drop in counter or explicit zero after positive
    reset_mask = (dv < 0) | ((v == 0) & (np.maximum.accumulate(v) > 0))
    # first and last markers for convenience
    events = [{'time': t[0], 'kind': 'start'}]
    events += [{'time': t[i], 'kind': 'reset'} for i in np.where(reset_mask)[0]]
    events += [{'time': t[-1], 'kind': 'end'}]
    out = pd.DataFrame(events).sort_values('time').drop_duplicates(subset=['time', 'kind'])
    return out.reset_index(drop=True)

def extract_events(df_fails: pd.DataFrame,
                   value_col: str = 'failsP_acum',
                   min_separation: float = 0.0) -> np.ndarray:
    """
    Convert cumulative counter into discrete event timestamps.
    - An event is counted when the counter increases (diff > 0).
    - Optionally collapse bursts closer than min_separation seconds into a single event.
    Returns a numpy array of event times (seconds).
    """
    df = df_fails[['time', value_col]].copy().sort_values('time')
    t = _ensure_time_seconds(df['time'])
    v = df[value_col].to_numpy(dtype=float, copy=False)
    dv = np.diff(v, prepend=v[0])
    # consider only positive jumps
    ev_times = t[dv > 0]

    if min_separation > 0 and ev_times.size:
        collapsed = [ev_times[0]]
        for x in ev_times[1:]:
            if x - collapsed[-1] >= min_separation:
                collapsed.append(x)
        ev_times = np.array(collapsed, dtype=float)
    return ev_times

# -----------------------------
# Binning by resets (k-resets per bin)
# -----------------------------

def build_bins_by_resets(reset_table: pd.DataFrame,
                         k_multiple: int = 1) -> List[Tuple[float, float]]:
    """
    Build bins from reset-to-reset intervals. Group every k_multiple consecutive
    intervals into one bin. Returns list of (t_start, t_end).
    """
    times = reset_table['time'].to_numpy(dtype=float)
    # segments are between consecutive markers; we treat from each 'start/reset' to next 'reset/end'
    seg_starts = times[:-1]
    seg_ends   = times[1:]
    segs = [(a, b) for a, b in zip(seg_starts, seg_ends) if b > a]

    if k_multiple <= 1:
        return segs

    grouped = []
    acc_start = None
    count = 0
    for (a, b) in segs:
        if acc_start is None:
            acc_start = a
        count += 1
        if count == k_multiple:
            grouped.append((acc_start, b))
            acc_start = None
            count = 0
    # if tail remains, close it with the last seen end
    if acc_start is not None:
        grouped.append((acc_start, segs[-1][1]))
    return grouped

# -----------------------------
# Poisson MLE and exact CIs
# -----------------------------

def garwood_ci_counts(k: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Exact (Garwood) confidence interval for a Poisson count k with coverage 1-alpha.
    Returns (lo, hi) for the mean count mu.
    """
    if k < 0 or int(k) != k:
        raise ValueError("k must be a non-negative integer")
    k = int(k)
    if k == 0:
        lo = 0.0
        hi = 0.5 * chi2.ppf(1 - alpha/2.0, 2*(k+1))
    else:
        lo = 0.5 * chi2.ppf(alpha/2.0, 2*k)
        hi = 0.5 * chi2.ppf(1 - alpha/2.0, 2*(k+1))
    return (lo, hi)

def garwood_ci_rate(k: int, exposure: float, alpha: float = 0.05) -> Tuple[float, float]:
    """Garwood CI for a rate lambda, given count k over exposure E (time or fluence)."""
    lo_c, hi_c = garwood_ci_counts(k, alpha=alpha)
    if exposure <= 0 or not np.isfinite(exposure):
        return (np.nan, np.nan)
    return (lo_c / exposure, hi_c / exposure)

from dataclasses import dataclass

@dataclass
class PoissonRateEstimate:
    k: int
    exposure: float
    lam_hat: float
    var: float
    se: float
    rel_error: float
    ci_lo: float
    ci_hi: float

def poisson_rate_mle(k: int, exposure: float, alpha: float = 0.05) -> PoissonRateEstimate:
    """
    MLE for rate lambda with count k over exposure E:
      lam_hat = k / E
      Var(lam_hat) approx k / E**2  (delta method), SE = sqrt(k)/E
      Relative error = SE / lam_hat = 1/sqrt(k) for k>0
    CI: exact Garwood
    """
    if exposure <= 0 or not np.isfinite(exposure):
        return PoissonRateEstimate(k, exposure, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan)
    lam_hat = k / exposure
    var = (k / (exposure**2)) if k > 0 else 0.0
    se = (math.sqrt(k) / exposure) if k > 0 else 0.0
    rel_error = (se / lam_hat) if k > 0 and lam_hat > 0 else (np.inf if k==0 else np.nan)
    ci_lo, ci_hi = garwood_ci_rate(k, exposure, alpha=alpha)
    return PoissonRateEstimate(k, exposure, lam_hat, var, se, rel_error, ci_lo, ci_hi)

# -----------------------------
# Exposure & bin aggregation
# -----------------------------

def _interval_slice_mask(t: np.ndarray, a: float, b: float) -> np.ndarray:
    return (t >= a) & (t < b)

def aggregate_exposure_and_counts(df_beam: pd.DataFrame,
                                  df_fails: pd.DataFrame,
                                  bins: List[Tuple[float, float]],
                                  n_subsystems: int,
                                  flux_col: str = 'N1MeV_dose_rate',
                                  beam_on_col: str = 'beam_on',
                                  ref_flux: Optional[float] = None,
                                  min_separation: float = 0.0) -> pd.DataFrame:
    """
    For each bin [a,b), compute:
      - time_exposure: sum of dt when beam_on==1
      - eq_time_exposure: sum dt * (flux / ref_flux) when beam_on==1
      - k: number of (collapsed) events in [a,b)
      - n_subsystems copied for later normalization
    Returns a dataframe with per-bin stats.
    """
    beam = df_beam.copy().sort_values('time')
    fails = df_fails.copy().sort_values('time')

    t_beam = _ensure_time_seconds(beam['time'])
    dt = _ensure_dt(beam)
    beam['_t'] = t_beam
    beam['_dt'] = dt
    if beam_on_col not in beam.columns:
        beam[beam_on_col] = 1
    if flux_col not in beam.columns:
        # treat as flat reference if missing
        beam[flux_col] = 1.0

    # reference flux = median over beam-on intervals if not provided
    if ref_flux is None:
        ref_flux = np.nanmedian(beam.loc[beam[beam_on_col]==1, flux_col].to_numpy(dtype=float))

    # event times (collapsed if min_separation set)
    ev_times = extract_events(fails, value_col='failsP_acum', min_separation=min_separation)

    rows = []
    for (a, b) in bins:
        m = _interval_slice_mask(t_beam, a, b) & (beam[beam_on_col].to_numpy(dtype=bool))
        # raw time exposure where beam was on
        time_exp = np.nansum(beam.loc[m, '_dt'].to_numpy(dtype=float))
        # equivalent-time exposure weighted by flux relative to ref
        rel_flux = beam.loc[m, flux_col].to_numpy(dtype=float) / (ref_flux if ref_flux>0 else 1.0)
        eq_time_exp = np.nansum(beam.loc[m, '_dt'].to_numpy(dtype=float) * rel_flux)

        k = int(np.sum((ev_times >= a) & (ev_times < b)))
        rows.append({
            't_start': a, 't_end': b, 't_mid': 0.5*(a+b),
            'k': k,
            'time_exposure': time_exp,
            'eq_time_exposure': eq_time_exp,
            'n_subsystems': n_subsystems
        })
    return pd.DataFrame(rows)

def bin_and_rate(df_beam: pd.DataFrame,
                 df_fails: pd.DataFrame,
                 n_subsystems: int,
                 flux_col: str = 'N1MeV_dose_rate',
                 beam_on_col: str = 'beam_on',
                 k_multiple: int = 1,
                 min_separation: float = 0.0,
                 ref_flux: Optional[float] = None,
                 alpha: float = 0.05) -> pd.DataFrame:
    """
    High-level convenience:
      1) detect resets
      2) build k-reset bins
      3) aggregate exposures & counts
      4) compute rate MLEs per bin (per-subsystem)
    Returns dataframe with columns:
      ['t_start','t_end','t_mid','k','time_exposure','eq_time_exposure',
       'lam_time','lam_time_lo','lam_time_hi','lam_eq','lam_eq_lo','lam_eq_hi']
    """
    resets = detect_resets(df_fails)
    bins = build_bins_by_resets(resets, k_multiple=k_multiple)
    agg = aggregate_exposure_and_counts(
        df_beam, df_fails, bins, n_subsystems,
        flux_col=flux_col, beam_on_col=beam_on_col,
        ref_flux=ref_flux, min_separation=min_separation
    )
    # normalize exposure by number of subsystems to get per-subsystem rates
    agg['time_exp_per_sub'] = agg['time_exposure'] * agg['n_subsystems']
    agg['eq_time_exp_per_sub'] = agg['eq_time_exposure'] * agg['n_subsystems']

    # per-bin MLEs + CIs
    lam_time, lam_time_lo, lam_time_hi = [], [], []
    lam_eq, lam_eq_lo, lam_eq_hi = [], [], []
    se_time, se_eq, rel_time, rel_eq = [], [], [], []

    for k, Et, Ee in zip(agg['k'].to_numpy(int),
                         agg['time_exp_per_sub'].to_numpy(float),
                         agg['eq_time_exp_per_sub'].to_numpy(float)):
        est_t = poisson_rate_mle(k, Et, alpha=alpha)
        est_e = poisson_rate_mle(k, Ee, alpha=alpha)
        lam_time.append(est_t.lam_hat); lam_time_lo.append(est_t.ci_lo); lam_time_hi.append(est_t.ci_hi)
        lam_eq.append(est_e.lam_hat);   lam_eq_lo.append(est_e.ci_lo);   lam_eq_hi.append(est_e.ci_hi)
        se_time.append(est_t.se); se_eq.append(est_e.se)
        rel_time.append(est_t.rel_error); rel_eq.append(est_e.rel_error)

    out = agg.copy()
    out['lam_time']    = lam_time
    out['lam_time_lo'] = lam_time_lo
    out['lam_time_hi'] = lam_time_hi
    out['lam_eq']      = lam_eq
    out['lam_eq_lo']   = lam_eq_lo
    out['lam_eq_hi']   = lam_eq_hi
    out['se_time']     = se_time
    out['se_eq']       = se_eq
    out['rel_time']    = rel_time
    out['rel_eq']      = rel_eq
    return out

# -----------------------------
# Trend test: constant rate vs. time trend (Poisson GLM with offset)
# -----------------------------

from dataclasses import dataclass

@dataclass
class TrendResult:
    beta0: float
    beta1: float
    se_beta1: float
    z_beta1: float
    p_value: float
    converged: bool
    n_bins: int

def fit_poisson_trend(bins_df: pd.DataFrame,
                      use_eq_time: bool = True,
                      alpha: float = 0.05) -> TrendResult:
    """
    Fit Poisson log-linear model:
      k_i ~ Poisson(mu_i),  log(mu_i) = beta0 + beta1 * t_mid_i + log(E_i),
    where E_i is exposure (time or eq_time) * n_subsystems (already present in bins_df
    as 'time_exp_per_sub' or 'eq_time_exp_per_sub').
    Tests H0: beta1 = 0 (constant rate over time).
    Returns point estimates and Wald z-test for beta1.
    """
    k = bins_df['k'].to_numpy(int)
    t = bins_df['t_mid'].to_numpy(float)
    E = (bins_df['eq_time_exp_per_sub'].to_numpy(float) if use_eq_time
         else bins_df['time_exp_per_sub'].to_numpy(float))

    # remove bins with zero exposure (can't inform the model)
    m = np.isfinite(E) & (E > 0)
    k, t, E = k[m], t[m], E[m]
    if k.size < 2:
        return TrendResult(np.nan, np.nan, np.nan, np.nan, np.nan, False, int(k.size))

    # center/scale t to improve numerics
    t_mean = np.mean(t)
    t_std  = np.std(t) if np.std(t) > 0 else 1.0
    x = (t - t_mean) / t_std
    offset = np.log(E)

    # Negative log-likelihood
    def nll(beta):
        b0, b1 = beta
        eta = b0 + b1 * x + offset
        mu = np.exp(eta)
        # const term (log k!) is dropped; NLL up to an additive constant
        return np.sum(mu - k * eta)

    res = minimize(nll, x0=np.array([np.log((k.sum()+1)/(E.sum()+1e-12)), 0.0]),
                   method='L-BFGS-B')
    converged = res.success
    b0, b1 = res.x

    # Numerical Hessian for SEs (approximate)
    eps = 1e-6
    def grad(beta):
        b0, b1 = beta
        eta = b0 + b1 * x + offset
        mu = np.exp(eta)
        g0 = np.sum(mu - k)
        g1 = np.sum((mu - k) * x)
        return np.array([g0, g1])

    # Hessian by finite differences on gradient
    H = np.zeros((2,2))
    for i in range(2):
        e = np.zeros(2); e[i] = eps
        gp = grad(res.x + e)
        gm = grad(res.x - e)
        H[:, i] = (gp - gm) / (2*eps)

    # Invert Hessian to get covariance (observed information)
    try:
        cov = np.linalg.inv(H)
        se_b1 = math.sqrt(abs(cov[1,1]))
    except np.linalg.LinAlgError:
        se_b1 = np.nan

    z = b1 / se_b1 if np.isfinite(se_b1) and se_b1 > 0 else np.nan

    # two-sided p-value under normal approx
    from math import erf, sqrt
    def two_sided_p(z):
        if not np.isfinite(z):
            return np.nan
        cdf = 0.5 * (1.0 + erf(abs(z) / sqrt(2.0)))
        return 2.0 * (1.0 - cdf)
    p = two_sided_p(z)

    # unpack in original time units (beta1 is per t_std units). We report slope per second:
    beta1_per_sec = b1 / (t_std if t_std > 0 else 1.0)
    se_beta1_per_sec = se_b1 / (t_std if t_std > 0 else 1.0)

    return TrendResult(beta0=b0, beta1=beta1_per_sec, se_beta1=se_beta1_per_sec,
                       z_beta1=z, p_value=p, converged=converged, n_bins=int(k.size))

def recommend_k_multiple(df_fails: pd.DataFrame,
                         target_events_per_bin: int = 5,
                         min_separation: float = 0.0) -> int:
    """
    Choose k_multiple (number of reset-intervals per bin) so that the median
    number of events per bin is close to target_events_per_bin.
    """
    resets = detect_resets(df_fails)
    bins_1 = build_bins_by_resets(resets, k_multiple=1)
    ev_times = extract_events(df_fails, min_separation=min_separation)
    # events per reset interval
    ev_counts = []
    for a, b in bins_1:
        ev_counts.append(int(np.sum((ev_times >= a) & (ev_times < b))))
    ev_counts = np.array(ev_counts, dtype=float)
    med_per_reset = np.nanmedian(ev_counts) if ev_counts.size else 0.0
    if med_per_reset <= 0:
        return 1
    k = int(np.ceil(target_events_per_bin / med_per_reset))
    return max(1, k)
