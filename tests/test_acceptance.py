\
import numpy as np, pandas as pd
from radbin.core import (
    compute_scaled_time_clipped, extract_event_times, build_and_summarize
)
from radbin.synth import synth_beam, synth_fails_from_hazard
from radbin.glm import poisson_trend_test

def assert_acceptance(df_beam, fails_df, res_df, use_scaled, rmax=1e4):
    # 1) N accounting + CI containment
    events = extract_event_times(fails_df)
    t = pd.to_datetime(events).sort_values().values
    edges = list(zip(res_df["t_start"], res_df["t_end"]))
    n_sum = sum(int(((t >= np.datetime64(a)) & (t < np.datetime64(b))).sum()) for a,b in edges)
    assert n_sum == int(res_df["N"].sum())
    bad = res_df[(res_df["T"]>0) & ~((res_df["lo"]<=res_df["rate"]) & (res_df["rate"]<=res_df["hi"]))]
    assert bad.empty
    # 2) scaling sanity
    beq = compute_scaled_time_clipped(df_beam, rmax=rmax)
    dt = pd.to_numeric(beq["dt"], errors="coerce").fillna(0)
    dteq = pd.to_numeric(beq["dt_eq"], errors="coerce").fillna(0)
    ratio = (dteq/dt).replace([np.inf,-np.inf], np.nan)
    ratio = ratio[dt>0]
    assert np.nanmax(ratio) <= rmax + 1e-9
    # 3) wall time consistency
    if not use_scaled and len(res_df)>0:
        S_T = res_df["T"].sum(); S_W = res_df["width_s"].sum()
        rel = abs(S_T - S_W)/max(S_W, 1e-9)
        assert rel <= 0.20

def test_plateau_and_bathtub_end_to_end():
    beam = synth_beam()
    failsP = synth_fails_from_hazard(beam, hazard_mode="plateau", plateau_level=0.02, rate_scale=0.8)
    failsB = synth_fails_from_hazard(beam, hazard_mode="bathtub", plateau_level=0.01, rate_scale=0.6)

    res_wall_P = build_and_summarize(beam, failsP, bin_mode="reset", T_source="wall")
    res_flu_P  = build_and_summarize(beam, failsP, bin_mode="fluence", n_bins=24, T_source="beam", min_events_per_bin=5)
    assert_acceptance(beam, failsP, res_wall_P, use_scaled=False)
    assert_acceptance(beam, failsP, res_flu_P,  use_scaled=True)

    res_flu_B = build_and_summarize(beam, failsB, bin_mode="fluence", n_bins=24, T_source="beam", min_events_per_bin=5)
    assert_acceptance(beam, failsB, res_flu_B, use_scaled=True)

    trP = poisson_trend_test(res_flu_P, x_col="t_mid")
    trB = poisson_trend_test(res_flu_B, x_col="t_mid")
    assert trP["p_value"] >= 0.001  # not too tiny
    assert trB["p_value"] <= 0.5    # allows detection room
