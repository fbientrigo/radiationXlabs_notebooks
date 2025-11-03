from .core import plot_cumulative_fails, errorbar_rates, plot_scaling_ratio

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def bar_rates(
    df_stats,
    y_var="gap_mean", # use rate alternatively
    n_var="gap_N",
    title=None,
    y_label="σ [(cm^2)/subsystem]",
    logy=False,
    alpha=0.55,
    capsize=4,
    exponential: bool = False,   # NEW: use SEM from μ (gap_mean) instead of Garwood
    show_err: bool = True        # NEW: toggle error bars on/off
):
    """
    Bar plot of per-bin rate with optional error bars.

    See Melanie Berg at the Hardened Electronics and Radiation Technology (HEART) Conference, Omaha NE, April 27th, 2023

    exponential=False  -> Garwood CI (asymmetric) using lo/hi columns.
        To be used when we are in a Poisson model

    exponential=True   -> symmetric SEM in rate-space using μ/√n from gaps:
                          SE(σ) ≈ σ / √n, with n = gap_N.
                          Falls back to n=N if gap_N is missing.
        To be used when we are in an exponential model
    """
    d = df_stats.copy()

    t0   = pd.to_datetime(d["t_start"])
    t1   = pd.to_datetime(d["t_end"])
    tmid = pd.to_datetime(d["t_mid"])
    width_days = (t1 - t0).dt.total_seconds() / 86400.0

    y  = pd.to_numeric(d[y_var], errors="coerce").astype(float)

    # use 1/mu for sigma


    # --- choose error bars
    yerr = None
    if show_err:
        if not exponential: # Poisson type model
            if title==None:
                title=r"$\sigma_{SEE}$"

            lo = pd.to_numeric(d["lo"], errors="coerce").astype(float)
            hi = pd.to_numeric(d["hi"], errors="coerce").astype(float)
            lower = np.clip(y - lo, 0, np.inf)
            upper = np.clip(hi - y, 0, np.inf)
            yerr = np.vstack([lower, upper])
        else:
            if title==None:
                title=r"$\sigma_{SEF_\mu}$"
            # SEM from μ and n, mapped to rate-space: SE(σ) ≈ σ / √n
            n = pd.to_numeric(d[n_var], errors="coerce").astype(float)
            n = n.where(n > 0, np.nan)  # avoid div/0
            sem_rate = y / np.sqrt(n)
            yerr = np.vstack([sem_rate, sem_rate])

    fig, ax = plt.subplots()
    
    


    # bars aligned to bin start with real width
    ax.bar(t0, y, width=width_days, align="edge", alpha=alpha,
           edgecolor="black", linewidth=0.6, zorder=2)

    if show_err and yerr is not None and np.isfinite(yerr).any():
        ax.errorbar(tmid, y, yerr=yerr, fmt="none", capsize=capsize, lw=1.0, zorder=3)

    # cosmetics
    mode_label = "Garwood CI" if not exponential else "SEM: σ/√n (from gaps)"
    ax.set_title(f"{title}\n[{mode_label}]")
    ax.set_ylabel(y_label)
    if logy:
        ax.set_yscale("log")
    fig.autofmt_xdate()
    plt.tight_layout()
    return ax
