from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple, Literal
import numpy as np
import pandas as pd
from scipy.stats import chi2

# -----------------------------
# Time parsing
# -----------------------------
def to_datetime_smart(series: pd.Series) -> pd.Series:
    """
    Parse datetimes from ISO strings, pandas datetime64, or epoch seconds/millis/micros/nanos.
    Heuristic for numeric:
      - if max > 1e18 -> ns
      - elif max > 1e15 -> us
      - elif max > 1e12 -> ms
      - elif max > 1e10 -> s (float allowed)
      - else: assume seconds
    """
    s = series.copy()
    if np.issubdtype(s.dtype, np.datetime64):
        return pd.to_datetime(s, errors="coerce")
    # Try parse strings first
    if s.dtype == object:
        # if objects are numeric-like strings, fall through to numeric
        try:
            sn = pd.to_numeric(s, errors="raise")
            s = sn
        except Exception:
            return pd.to_datetime(s, errors="coerce", utc=False)
    if np.issubdtype(s.dtype, np.number):
        x = pd.to_numeric(s, errors="coerce").astype("float64")
        m = np.nanmax(x) if np.isfinite(x).any() else 0.0
        if m > 1e18:
            unit = "ns"
        elif m > 1e15:
            unit = "us"
        elif m > 1e12:
            unit = "ms"
        elif m > 1e10:
            unit = "s"
        else:
            unit = "s"
        return pd.to_datetime(x, unit=unit, errors="coerce")
    # Fallback
    return pd.to_datetime(s, errors="coerce")

# -----------------------------
# Scaled time with guardrails
# -----------------------------
# -----------------------------
# Scaled time / exposure with guardrails
# -----------------------------
from typing import Literal

def compute_scaled_time_clipped(
    beam_df: pd.DataFrame,
    time_col: str = "time",
    dt_col: str = "dt",
    flux_col: str = "dHEH",
    beam_on_col: str = "beam_on",
    ref: Literal["median","mean","max"] = "median",
    floor_strategy: Literal["adaptive","fixed"] = "adaptive",
    min_frac: float = 0.05,
    rmax: float = 1e4,
    freeze_off: bool = True,
    start_at_first_on: bool = True,
    mode: Literal["ref_time", "fluence"] = "fluence",
) -> pd.DataFrame:
    """
    Devuelve una copia de beam_df con:
      - dt (s) asegurado
      - dt_eq
      - t_eq (acumulado)
      - scale_ratio = dt_eq/dt (donde dt>0)

    MODO "ref_time" (por defecto, comportamiento previo):
      * dt_eq = dt * clip(phi_ref / phi_eff, 0, rmax)
      * t_eq = sum(dt_eq)
      * scale_ratio = phi_ref / phi_eff   (cortado por rmax)
      * freeze_off => ratio = 0 cuando beam_off
      * start_at_first_on => ratio = 0 antes del primer beam_on

    MODO "fluence" (nuevo, para contar errores por exposición):
      * dt_eq = dPhi = phi_eff * dt
      * t_eq = Phi acumulada
      * scale_ratio = phi_eff             (≡ dt_eq/dt)
      * freeze_off => phi_eff = 0 cuando beam_off
      * start_at_first_on => phi_eff = 0 antes del primer beam_on

    Parámetros de referencia/piso:
      - phi_ref se calcula sobre muestras con beam_on==1, usando ref ∈ {median, mean, max}
      - floor_strategy="adaptive": piso = max(min_frac * phi_ref, 1e-12)
        (para evitar divisiones por ~0 en "ref_time" y ruido en "fluence")
      - floor_strategy="fixed": piso = max(min_frac, 1e-12)
    """
    df = beam_df.copy()
    df[time_col] = to_datetime_smart(df[time_col])
    df = df.sort_values(time_col).reset_index(drop=True)

    # Asegurar dt
    if dt_col not in df.columns or df[dt_col].isna().all():
        t = pd.to_datetime(df[time_col])
        dt = t.diff().dt.total_seconds().fillna(0).astype("float64")
        df[dt_col] = dt
    dt = pd.to_numeric(df[dt_col], errors="coerce").fillna(0).astype("float64") # los segundos quedan en flotantes

    # Señal de flujo y beam_on
    # Flujo (fluencia/s)
    phi = pd.to_numeric(df.get(flux_col, pd.Series(np.nan, index=df.index)), errors="coerce")

    bon = pd.to_numeric(df.get(beam_on_col, pd.Series(0, index=df.index)), errors="coerce").fillna(0).astype(int)

    # ---- phi_ref (sobre beam ON) --- valor de referencia
    phi_on = phi[bon == 1].dropna()
    if len(phi_on) == 0:
        phi_ref = np.nan
    else:
        if ref == "median":
            phi_ref = float(np.median(phi_on))
        elif ref == "mean":
            phi_ref = float(np.mean(phi_on))
        else:
            phi_ref = float(np.max(phi_on))

    # Piso de flujo (evita ruido y divisiones por ~0)
    if floor_strategy == "adaptive" and np.isfinite(phi_ref):
        phi_floor = max(min_frac * phi_ref, 1e-12)
    else:
        phi_floor = max(min_frac, 1e-12)

    # Versión "efectiva" para trabajar
    # Primero se elige phi que vendrá a ser df[flux_col]
    phi_eff = pd.to_numeric(phi, errors="coerce").fillna(0.0).clip(lower=phi_floor)

    # Congelar cuando beam_off (si se pide)
    if freeze_off:
        phi_eff = phi_eff.where(bon == 1, 0.0)

    # Cero antes del primer beam_on (si se pide)
    if start_at_first_on and (bon == 1).any():
        first_on_idx = int(np.argmax((bon == 1).to_numpy()))
        mask_before = np.arange(len(df)) < first_on_idx
        phi_eff = phi_eff.mask(mask_before, 0.0)

    if mode == "ref_time":
        # Ratio ref/eff (cap a rmax); anula contribuciones según flags
        # OJO: para el ratio usamos el phi_eff "no-zeroed" para evitar inf; luego aplicamos mascaras
        phi_for_ratio = pd.to_numeric(phi, errors="coerce").fillna(0.0).clip(lower=phi_floor)
        ratio = np.where(phi_for_ratio > 0,
                         (phi_ref / phi_for_ratio) if np.isfinite(phi_ref) else 1.0,
                         rmax)
        ratio = np.clip(ratio, 0.0, rmax)
        if freeze_off:
            ratio = np.where(bon == 1, ratio, 0.0)
        if start_at_first_on and (bon == 1).any():
            ratio = np.where(mask_before, 0.0, ratio)

        dt_eq = dt * ratio
        t_eq  = np.cumsum(dt_eq)
        scale_ratio = np.where(dt > 0, dt_eq / dt, np.nan)  # ≡ ratio

    elif mode == "fluence":
        # Exposición de fluencia: dPhi = phi_eff * dt; Phi acumulada
        dPhi = dt * phi_eff.to_numpy(dtype=float)
        Phi  = np.cumsum(dPhi)
        dt_eq = dPhi
        t_eq  = Phi
        scale_ratio = np.where(dt > 0, dt_eq / dt, np.nan)  # ≡ phi_eff

    else:
        raise ValueError('mode must be "ref_time" or "fluence"')

    out = df.copy()
    out["dt"] = dt
    out["dt_eq"] = dt_eq
    out["t_eq"] = t_eq
    out["scale_ratio"] = scale_ratio
    return out


# -----------------------------
# Event extraction (from cumulative)
# -----------------------------
def extract_event_times(
    fails_df: pd.DataFrame,
    time_col: str = "time",
    cum_col: str  = "failsP_acum"
) -> pd.Series:
    """
    From monotonically non-decreasing cumulative counter, emit one timestamp per increment.
    If negatives occur (resets), they are clipped to 0 increments.
    """
    f = fails_df.copy()
    t = to_datetime_smart(f[time_col])
    c = pd.to_numeric(f[cum_col], errors="coerce").ffill().fillna(0).astype("int64")
    dc = c.diff().fillna(c.iloc[0]).astype("int64")
    dc = dc.clip(lower=1e-12)
    # Expand timestamps by counts
    times = []
    for ti, k in zip(t, dc):
        if k > 0:
            times.extend([ti] * int(k))
    return pd.Series(times, name="event_time", dtype="datetime64[ns]")

# -----------------------------
# Reset detection & binning
# -----------------------------
def detect_resets(
    fails_df: pd.DataFrame,
    time_col: str = "time",
    cum_col: str  = "failsP_acum",
    aux_cols = ("lfsrTMR",),
    min_gap_s: float = 30.0,
    lfsr_cluster_rate_hz: float = 50.0,
) -> List[pd.Timestamp]:
    """
    Detect reset boundaries using:
      - drops in cumulative counter
      - zero after positive
      - edges/toggles in auxiliary flag columns (e.g., lfsrTMR)
    Cluster events closer than min_gap_s.
    Returns sorted list of boundary timestamps.
    """
    f = fails_df.copy().sort_values(time_col)
    t = to_datetime_smart(f[time_col])
    c = pd.to_numeric(f[cum_col], errors="coerce").ffill().fillna(0)
    dc = c.diff().fillna(0)

    cand = []
    # counter drops or zeros after positive
    drops = (dc < 0) | ((c == 0) & (c.shift(1, fill_value=0) > 0))
    cand.extend(list(t[drops]))

    # auxiliary edges
    for col in aux_cols:
        if col in f.columns:
            a = pd.to_numeric(f[col], errors="coerce").ffill().fillna(0)
            edges = (a != a.shift(1)).fillna(False)
            edge_times = t[edges]
            cand.extend(list(edge_times))

    if not cand:
        return []

    # cluster by min_gap_s
    cand = sorted(pd.to_datetime(pd.Series(cand)).dropna().tolist())
    clustered = [cand[0]]
    for ts in cand[1:]:
        if (ts - clustered[-1]).total_seconds() >= min_gap_s:
            clustered.append(ts)
        else:
            # If too close, keep the earlier one (or prefer rising edges by heuristic)
            continue

    # Optional: thin very fast chatter by lfsr rate (~50 Hz => 0.02 s)
    chatter_gap = 1.0 / max(lfsr_cluster_rate_hz, 1e-6)
    final = [clustered[0]]
    for ts in clustered[1:]:
        if (ts - final[-1]).total_seconds() >= chatter_gap:
            final.append(ts)

    return final

def build_bins_reset_locked(reset_bounds: List[pd.Timestamp], k_multiple: int = 1) -> List[pd.Timestamp]:
    """
    Build bin edges that align to every k-th reset boundary.
    Assumes reset_bounds is sorted. Returns list of edges (timestamps).
    """
    if not reset_bounds:
        return []
    resets = sorted(pd.to_datetime(pd.Series(reset_bounds)).dropna().tolist())
    edges = [resets[0]]
    for i, ts in enumerate(resets[1:], start=1):
        if i % k_multiple == 0:
            edges.append(ts)
    # Ensure last edge
    if edges[-1] != resets[-1]:
        edges.append(resets[-1])
    return edges

def build_bins_equal_fluence(beam_eq: pd.DataFrame, n_bins: int) -> List[pd.Timestamp]:
    """
    Build edges so that scaled time (t_eq) is split into ~equal segments.
    """
    beq = beam_eq.sort_values("time")
    t = pd.to_datetime(beq["time"])
    teq = pd.to_numeric(beq["t_eq"], errors="coerce").fillna(0).to_numpy()
    if len(teq) == 0 or teq[-1] <= 0:
        return [t.iloc[0], t.iloc[-1]] if len(t) >= 2 else list(t.values)
    total = teq[-1]
    qs = np.linspace(0, total, n_bins + 1)
    edges = []
    j = 0
    for q in qs:
        # Find first index with teq >= q
        while j < len(teq) - 1 and teq[j] < q:
            j += 1
        edges.append(t.iloc[j])
    # Deduplicate while preserving order
    out = []
    seen = set()
    for e in edges:
        if e.value not in seen:
            out.append(e)
            seen.add(e.value)
    if len(out) < 2:
        out = [t.iloc[0], t.iloc[-1]]
    return out

def build_bins_equal_count(event_times: pd.Series, target_N: int) -> List[pd.Timestamp]:
    """
    Build edges so each bin contains about target_N events.
    """
    et = pd.to_datetime(pd.Series(event_times).dropna()).sort_values().reset_index(drop=True)
    if len(et) == 0:
        return []
    k = max(int(target_N), 1)
    edges = [et.iloc[0]]
    for i in range(k, len(et), k):
        edges.append(et.iloc[min(i, len(et)-1)])
    if edges[-1] != et.iloc[-1]:
        edges.append(et.iloc[-1])
    return edges

# -----------------------------
# Per-bin Poisson rate with Garwood CI
# -----------------------------
@dataclass
class BinStat:
    t_start: pd.Timestamp
    t_end: pd.Timestamp
    N: int
    T: float
    rate: float
    lo: float
    hi: float

def garwood_rate_ci(N: int, T: float, alpha: float = 0.32) -> Tuple[float, float]:
    """
    Exact Poisson (Garwood) CI on the rate λ = μ/T with μ ~ Poisson.
    When N=0, lower=0.
    """
    eps = 1e-12
    if T <= 0:
        return (np.nan, np.nan)
    if N < 0:
        N = 0
    lower_mu = 0.0 if N == 0 else 0.5 * chi2.ppf(alpha / 2.0, 2 * N)
    upper_mu = 0.5 * chi2.ppf(1.0 - alpha / 2.0, 2 * (N + 1))
    return (lower_mu / max(T, eps), upper_mu / max(T, eps))

# -----------------------------
# Summarize and orchestrate
# -----------------------------
def _count_events_in_interval(event_times_np, a: np.datetime64, b: np.datetime64) -> int:
    return int(((event_times_np >= a) & (event_times_np < b)).sum())

def _sum_time_in_interval(df_timebase: pd.DataFrame, a: pd.Timestamp, b: pd.Timestamp, use_scaled: bool) -> float:
    """
    Sum either scaled seconds (dt_eq) or wall-clock seconds between [a, b).
    """
    df = df_timebase[(df_timebase["time"] >= a) & (df_timebase["time"] < b)]
    if use_scaled:
        return float(pd.to_numeric(df["dt_eq"], errors="coerce").fillna(0).sum())
    else:
        # wall time from timestamps
        if len(df) == 0:
            return max(0.0, (b - a).total_seconds())
        # include gaps by using edges: total from min(time,a) to min(last,b)
        times = pd.to_datetime(df["time"]).tolist()
        times = [a] + times + [b]
        return float((times[-1] - times[0]).total_seconds())

def summarize_bins(
    event_times: pd.Series,
    bin_edges: List[pd.Timestamp],
    timebase_df: Optional[pd.DataFrame],
    use_scaled_time: bool,
    T_source: Literal["beam","wall"] = "beam",
    alpha: float = 0.32
) -> List[BinStat]:
    et = pd.to_datetime(pd.Series(event_times).dropna()).sort_values().reset_index(drop=True)
    if len(bin_edges) < 2:
        return []
    edges = sorted(pd.to_datetime(pd.Series(bin_edges)).tolist())
    # Ensure coverage of events: extend ends if needed
    if len(et) > 0:
        tmin = min(edges[0], et.iloc[0])
        tmax = max(edges[-1], et.iloc[-1] + pd.Timedelta(nanoseconds=1))
    else:
        tmin, tmax = edges[0], edges[-1]
    if edges[0] > tmin:
        edges = [tmin] + edges
    if edges[-1] < tmax:
        edges = edges + [tmax]

    # Event times ndarray for quick counting
    et_np = et.to_numpy(dtype="datetime64[ns]")
    stats: List[BinStat] = []
    for i in range(len(edges)-1):
        a, b = edges[i], edges[i+1]
        if a >= b:
            continue
        N = _count_events_in_interval(et_np, np.datetime64(a), np.datetime64(b))
        if T_source == "beam" and timebase_df is not None:
            T = _sum_time_in_interval(timebase_df, a, b, use_scaled=use_scaled_time)
        else:
            T = max(0.0, (b - a).total_seconds())
        rate = (N / T) if T > 0 else np.nan
        lo, hi = garwood_rate_ci(N, T, alpha=alpha)
        stats.append(BinStat(a, b, int(N), float(T), float(rate), float(lo), float(hi)))
    return stats

def _merge_bins_until(stats: List[BinStat], min_events: int) -> List[BinStat]:
    if min_events is None or min_events <= 0:
        return stats
    merged: List[BinStat] = []
    acc = None
    for s in stats:
        if acc is None:
            acc = s
            continue
        cand = acc
        if cand.N >= min_events:
            merged.append(cand)
            acc = s
        else:
            # merge
            N = cand.N + s.N
            T = cand.T + s.T
            rate = N / T if T > 0 else np.nan
            lo, hi = garwood_rate_ci(N, T, alpha=0.32)
            acc = BinStat(cand.t_start, s.t_end, N, T, rate, lo, hi)
    if acc is not None:
        merged.append(acc)
    # It might happen first bin still < min_events; merge left-to-right only once.
    # Users can rebin with different params if needed.
    return merged

import numpy as np
import pandas as pd
from typing import Optional, Tuple, List, Literal

# --- util: detectar columna de fluencia acumulada en beq ---
def _find_exposure_col(beq: pd.DataFrame) -> str:
    candidates = ["HEH"]
    for c in candidates:
        if c in beq.columns and np.issubdtype(beq[c].dtype, np.number):
            return c
    # último recurso: si hay exactamente una numérica además de dose_rate, usarla
    num_cols = [c for c in beq.columns if np.issubdtype(beq[c].dtype, np.number)]
    for c in num_cols:
        if c not in ("HEH_dose_rate", "dose_rate"):
            return c
    raise ValueError("No pude encontrar una columna de fluencia acumulada en beq.")

# --- util: interpolador Φ(t) monótono sobre timestamps ---
def _build_phi_interpolator(beq: pd.DataFrame):
    if "time" not in beq.columns:
        raise ValueError("beq debe tener columna 'time' (datetime64).")
    col = _find_exposure_col(beq)
    df = beq.sort_values("time").dropna(subset=["time", col]).copy()
    # eje en segundos (float) para np.interp
    t_sec = df["time"].astype("int64", copy=False) / 1e9
    phi = df[col].astype(float).values
    # aseguramos monotonicidad no estricta
    phi = np.maximum.accumulate(phi)
    def phi_at(ts: pd.Timestamp) -> float:
        x = np.array([ts.value / 1e9], dtype=float)
        # extrapolación lineal en extremos (np.interp lo hace con valores de borde)
        return float(np.interp(x, t_sec, phi))
    return phi_at

# --- util: ∆Φ recortadas por bin ---
def _inter_error_fluence_stats(
    events: List[pd.Timestamp],
    beq: pd.DataFrame,
    bin_edges: List[pd.Timestamp],
) -> List[dict]:
    phi_at = _build_phi_interpolator(beq)
    events = sorted([pd.Timestamp(e) for e in events])
    # generamos segmentos entre errores consecutivos
    segments = []
    for i in range(len(events) - 1):
        t0, t1 = events[i], events[i+1]
        if t1 <= t0:
            continue
        segments.append((t0, t1))

    # para cada bin, recortar y acumular estadísticas
    out: List[dict] = []
    for a, b in zip(bin_edges[:-1], bin_edges[1:]):
        gaps = []
        # recorremos segmentos que intersectan [a,b]
        # condición de intersección: (t0 < b) and (t1 > a)
        for t0, t1 in segments:
            if (t0 < b) and (t1 > a):
                start = max(t0, a)
                end   = min(t1, b)
                if end > start:
                    dphi = phi_at(end) - phi_at(start)
                    # permitimos min clip numérico
                    if dphi < 0:
                        dphi = 0.0
                    gaps.append(dphi)

        if len(gaps) == 0:
            out.append({
                "gap_N": 0, "gap_sum": 0.0, "gap_mean": np.nan, "gap_median": np.nan,
                "gap_p10": np.nan, "gap_p90": np.nan, "gap_p99": np.nan,
                "gap_min": np.nan, "gap_max": np.nan
            })
        else:
            g = np.asarray(gaps, dtype=float)
            out.append({
                "gap_N": int(g.size),
                "gap_sum": float(g.sum()),
                "gap_mean": float(g.mean()),
                "gap_median": float(np.median(g)),
                "gap_p10": float(np.percentile(g, 10)),
                "gap_p90": float(np.percentile(g, 90)),
                "gap_p99": float(np.percentile(g, 99)),
                "gap_min": float(g.min()),
                "gap_max": float(g.max()),
            })
    return out

# =============== TU FUNCIÓN CON EXTENSIÓN DE FLUENCIA ENTRE ERRORES ===============
def build_and_summarize(
    df_beam: pd.DataFrame,
    fails_df: pd.DataFrame,
    *,
    bin_mode: Literal["fluence","reset","count"] = "fluence",
    k_multiple: int = 1,
    n_bins: int = 30,
    target_N: int = 100,
    flux_col: str = "HEH_dose_rate",
    area_norm: Optional[Tuple[int,int]] = None,  # (A_run, A_ref)
    alpha: float = 0.05,
    T_source: Literal["beam","wall"] = "beam",
    scaled_time_fn = compute_scaled_time_clipped,
    min_events_per_bin: Optional[int] = None,
    # --- nuevo: umbral de exposición por bin (solo aplica si use_scaled=True) ---
    min_exposure_per_bin: Optional[float] = None,
) -> pd.DataFrame:
    """
    Igual que antes, pero **agrega** por bin estadísticas de *fluencia entre errores*:
      gap_N, gap_sum, gap_mean, gap_median, gap_p10, gap_p90, gap_p99, gap_min, gap_max
    """

    try:
        beq = scaled_time_fn(df_beam, flux_col=flux_col)
    except TypeError:
        beq = scaled_time_fn(df_beam)


    events = extract_event_times(fails_df)

    if bin_mode == "fluence": #  < ------
        edges = build_bins_equal_fluence(beq, n_bins=n_bins)
        use_scaled = True

    elif bin_mode == "reset":
        resets = detect_resets(fails_df)
        if not resets:
            t_all = pd.to_datetime(pd.concat([df_beam["time"], fails_df["time"]]))
            edges = [t_all.min(), t_all.max()]
        else:
            edges = build_bins_reset_locked(resets, k_multiple=k_multiple)
        use_scaled = (T_source == "beam")
    elif bin_mode == "count":
        edges = build_bins_equal_count(events, target_N=target_N)
        use_scaled = (T_source == "beam")
    else:
        raise ValueError("Unknown bin_mode")

    stats = summarize_bins(
        events,
        edges,
        timebase_df=beq,
        use_scaled_time=use_scaled,
        T_source=T_source,
        alpha=alpha
    )

    # --- fusión por exposición mínima ---
    if (min_exposure_per_bin is not None and min_exposure_per_bin > 0
        and use_scaled and T_source == "beam"):
        merged: List[BinStat] = []
        cur = None
        for s in stats:
            if cur is None:
                cur = s
                continue
            if cur.T < min_exposure_per_bin:
                N = cur.N + s.N
                T = cur.T + s.T
                rate = (N / T) if T > 0 else float('nan')
                lo, hi = garwood_rate_ci(N, T, alpha=alpha)
                cur = BinStat(cur.t_start, s.t_end, N, T, rate, lo, hi)
            else:
                merged.append(cur)
                cur = s
        if cur is not None:
            if cur.T < min_exposure_per_bin and merged:
                last = merged.pop()
                N = last.N + cur.N
                T = last.T + cur.T
                rate = (N / T) if T > 0 else float('nan')
                lo, hi = garwood_rate_ci(N, T, alpha=alpha)
                cur = BinStat(last.t_start, cur.t_end, N, T, rate, lo, hi)
            merged.append(cur)
        stats = merged

    # --- fusión por mínimo de eventos (si se pide) ---
    stats = _merge_bins_until(stats, min_events=min_events_per_bin)

    # --- NUEVO: fluencia entre errores recortada por bin ---
    gap_stats = _inter_error_fluence_stats(events, beq, [s.t_start for s in stats] + [stats[-1].t_end] if stats else [])

    # --- construir DataFrame ---
    rows = []
    for i, s in enumerate(stats):
        width_s = (s.t_end - s.t_start).total_seconds()
        t_mid = s.t_start + (s.t_end - s.t_start) / 2
        base = {
            "t_start": s.t_start, "t_end": s.t_end, "N": s.N, "T": s.T,
            "rate": (s.N / s.T) if s.T > 0 else float("nan"),
            "lo": s.lo, "hi": s.hi,
            "t_mid": t_mid, "width_s": width_s
        }
        # adjuntar stats de gaps si existen
        if gap_stats:
            base.update(gap_stats[i])
        rows.append(base)

    df = pd.DataFrame(rows)

    # --- normalización por área (se aplica a tasas; los gaps en ∆Φ no se escalan por área) ---
    if area_norm is not None and len(df) > 0:
        A_run, A_ref = area_norm
        if A_run is not None and A_ref is not None and A_run > 0:
            factor = float(A_ref) / float(A_run)
            df["rate"] = df["rate"] * factor
            df["lo"]   = df["lo"]   * factor
            df["hi"]   = df["hi"]   * factor
            # Nota: gap_* permanecen en unidades de fluencia (no normalizamos por área aquí)

    return df




# -----------------------------
# Diagnostics & plots
# -----------------------------
def inspect_scaled_time(beam_eq: pd.DataFrame, label: str, clip_warn_ratio: float = 1e2) -> None:
    r = pd.to_numeric(beam_eq.get("scale_ratio", np.nan), errors="coerce")
    rr = r.replace([np.inf, -np.inf], np.nan).dropna()
    if len(rr) == 0:
        print(f"[inspect_scaled_time] {label}: no valid ratios")
        return
    med = float(np.median(rr)); p99 = float(np.nanpercentile(rr, 99))
    mx = float(np.nanmax(rr))
    print(f"[inspect_scaled_time] {label}: median={med:.3g}, p99={p99:.3g}, max={mx:.3g}")
    if mx > clip_warn_ratio:
        print(f"[inspect_scaled_time] WARNING: max ratio {mx:.2f} > {clip_warn_ratio} (check floors/rmax)")

def check_real_output(df_out: pd.DataFrame, name: str, use_scaled: bool, tol_ratio: float = 0.20) -> None:
    if len(df_out) == 0:
        print(f"[check_real_output] {name}: empty output")
        return
    bad = df_out[(df_out["T"] > 0) & ~((df_out["lo"] <= df_out["rate"]) & (df_out["rate"] <= df_out["hi"]))]
    if len(bad) > 0:
        print(f"[check_real_output] {name}: {len(bad)} rows have rate outside CI (shouldn't happen)")
    if not use_scaled:
        S_T = float(df_out["T"].sum()); S_W = float(df_out["width_s"].sum())
        rel = abs(S_T - S_W) / max(S_W, 1e-9)
        if rel <= tol_ratio:
            print(f"[check_real_output] {name}: wall-time sum consistency OK (rel diff {rel:.2%})")
        else:
            print(f"[check_real_output] {name}: wall-time sum consistency BAD (rel diff {rel:.2%})")

def conservation_checks(
    events: pd.Series,
    edges: List[pd.Timestamp],
    beam_eq: pd.DataFrame,
    use_scaled: bool
) -> None:
    et = pd.to_datetime(pd.Series(events).dropna()).sort_values().to_numpy(dtype="datetime64[ns]")
    # Count conservation
    tot = len(et)
    partials = 0
    for a, b in zip(edges[:-1], edges[1:]):
        partials += int(((et >= np.datetime64(a)) & (et < np.datetime64(b))).sum())
    print(f"[conservation_checks] Events: total={tot}, by-bins={partials} (must match)")

# -----------------------------
# Plotting helpers (matplotlib-only, one chart per figure)
# -----------------------------
import matplotlib.pyplot as plt

def plot_cumulative_fails(fails_df, time_col="time", cum_col="failsP_acum", title="Cumulative fails"):
    ff = fails_df.copy().sort_values(time_col)
    t = to_datetime_smart(ff[time_col])
    c = pd.to_numeric(ff[cum_col], errors="coerce").ffill().fillna(0)
    plt.figure()
    plt.plot(t, c, lw=1.5)
    plt.xlabel("Time")
    plt.ylabel(cum_col)
    plt.title(title)
    plt.tight_layout()

def errorbar_rates(df_stats, x_col="t_mid", y_col="rate", lo_col="lo", hi_col="hi", title="Rate per bin",
                   xlabel=r"$T$ime",ylabel=r"$\sigma=1/\mu$"):
    ds = df_stats.copy()
    x = pd.to_datetime(ds[x_col])
    y = pd.to_numeric(ds[y_col], errors="coerce")
    lo = pd.to_numeric(ds[lo_col], errors="coerce")
    hi = pd.to_numeric(ds[hi_col], errors="coerce")
    yerr = np.vstack([y - lo, hi - y])
    plt.figure()
    plt.errorbar(x, y, yerr=yerr, fmt="o", capsize=3)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()

def plot_scaling_ratio(df_beam, flux_col="HEH_dose_rate", label="Scaling ratio"):
    beq = compute_scaled_time_clipped(df_beam, flux_col=flux_col)
    t = to_datetime_smart(beq["time"])
    r = pd.to_numeric(beq["scale_ratio"], errors="coerce")
    plt.figure()
    plt.plot(t, r, lw=1.2)
    plt.xlabel("Time")
    plt.ylabel("scale_ratio = dt_eq / dt")
    plt.title(label)
    plt.tight_layout()
