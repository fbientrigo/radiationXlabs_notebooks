import numpy as np, pandas as pd
from .core import compute_scaled_time_clipped

def synth_beam(start="2025-01-01 09:00:00", hours=8, step_s=5.0,
               on_blocks=((0,2),(3,5),(6,8)),
               flux_base=1.0, flux_pulse=((1.0,1.5),(3.2,0.4),(6.5,2.0)),
               flux_noise=0.1, seed=7):
    rng = np.random.default_rng(seed)
    t0 = pd.Timestamp(start)
    n = int(hours*3600/step_s)
    times = [t0 + pd.Timedelta(seconds=i*step_s) for i in range(n)]
    dt = np.full(n, step_s, float)
    beam_on = np.zeros(n, int)
    for a,b in on_blocks:
        i0 = int(a*3600/step_s); i1 = int(b*3600/step_s)
        beam_on[i0:i1] = 1
    xh = np.arange(n)*step_s/3600.0
    flux = np.full(n, flux_base, float)
    for center, amp in flux_pulse:
        flux += amp*np.exp(-0.5*((xh-center)/0.15)**2)
    flux += rng.normal(0, flux_noise, size=n)
    flux = np.clip(flux, 1e-6, None)
    return pd.DataFrame({"time": times, "dt": dt, "HEH_dose_rate": flux, "beam_on": beam_on})

def synth_fails_from_hazard(df_beam, hazard_mode="bathtub", rate_scale=0.2,
                            early_decay=1.2, wear_growth=1.2, plateau_level=0.03,
                            reset_every_s=None, seed=11):
    rng = np.random.default_rng(seed)
    beq = compute_scaled_time_clipped(df_beam, freeze_off=True, start_at_first_on=True)
    t = pd.to_datetime(beq["time"])
    dt = pd.to_numeric(beq["dt"], errors="coerce").fillna(0).to_numpy()
    dteq = pd.to_numeric(beq["dt_eq"], errors="coerce").fillna(0).to_numpy()
    teq = pd.to_numeric(beq["t_eq"], errors="coerce").fillna(0).to_numpy()
    if hazard_mode == "bathtub":
        eps = 1.0
        early = (early_decay) / np.power(teq + eps, 0.7)
        wear  = (wear_growth) * np.power(teq/teq.max() if teq.max()>0 else 0, 2.0)
        lam_eq = plateau_level + early + wear
    else:
        lam_eq = np.full_like(teq, plateau_level, float)
    mu = lam_eq * dteq * rate_scale
    n_events = rng.poisson(mu)
    ev_times = []
    for i, k in enumerate(n_events):
        if k <= 0 or dt[i] <= 0: 
            continue
        start_i = t.iloc[i]
        for _ in range(int(k)):
            u = rng.uniform(0, dt[i])
            ev_times.append(start_i + pd.Timedelta(seconds=float(u)))
    ev_times.sort()
    rows = []; c=0
    for et in ev_times:
        c+=1; rows.append((et, c))
    out = pd.DataFrame(rows, columns=["time","failsP_acum"])
    if reset_every_s is not None and len(ev_times) > 0:
        toggles=[]; last=0; last_t=ev_times[0]
        for et in ev_times:
            if (et - last_t).total_seconds() >= reset_every_s:
                last = 1 - last
                last_t = et
            toggles.append(last)
        out["lfsrTMR"] = toggles
    return out
