import numpy as np
import pandas as pd
from scipy.stats import chi2, norm
import statsmodels.api as sm

# ========= Utilidad: IC de Garwood para tasas (para tus plots) =========
def garwood_rate_ci(n, exposure, alpha=0.35):
    """
    Intervalo exacto tipo Garwood para la TASA = N / exposure.
    n: array-like de conteos (enteros)
    exposure: array-like de exposiciones (>0)
    alpha: 1 - nivel de confianza (ej. 0.35 → 65% CI, útil en gráficos)
    """
    n = np.asarray(n, dtype=int)
    exp = np.asarray(exposure, dtype=float)
    if np.any(exp <= 0):
        raise ValueError("Todas las exposiciones deben ser > 0.")
    lo = 0.5 * chi2.ppf(alpha/2, 2*n) / exp
    hi = 0.5 * chi2.ppf(1 - alpha/2, 2*(n + 1)) / exp
    lo = np.where(n == 0, 0.0, lo)  # convención común
    return lo, hi


# ========= Utilidad: TOST para equivalencia práctica en beta1 =========
def tost_equivalence_beta1(beta1, se1, delta_log, alpha=0.05):
    """
    Test TOST bilateral para equivalencia en el coeficiente beta1 (escala log).
    H0: |beta1| >= delta_log  vs  H1: |beta1| < delta_log
    Retorna p-valor TOST (máx de las dos unilaterales) y booleano de equivalencia.
    """
    z1 = (beta1 + delta_log) / se1       # prueba beta1 > -delta
    z2 = (delta_log - beta1) / se1       # prueba beta1 < +delta
    p1 = 1 - norm.cdf(z1)
    p2 = 1 - norm.cdf(z2)
    p_tost = max(p1, p2)
    return {"p_tost": float(p_tost), "equivalent_at_alpha": bool(p_tost < alpha)}


# ========= GLM Poisson mejorado (robusto, AIC, LRT, TOST, checks) =========
def poisson_trend_test_plus(
    df_stats: pd.DataFrame,
    count: str = "N",
    exposure: str = "T",
    time_col: str = "t_mid",
    alpha: float = 0.05,
    se_method: str = "robust",        # {"robust", "pearson", "mle"}
    use_lrt: bool = True,             # LRT con Poisson MLE (deviance)
    equivalence_rr: float = None,     # p.ej., 1.01 → ±1% por hora como irrelevante
    standardize_time: bool = False,   # además de "por hora", entrega beta por SD(t)
    overdispersion_threshold: float = 1.5
) -> dict:
    """
    Ajusta GLM Poisson log-link con offset=log(exposure) para probar tendencia temporal.
    Devuelve slope en log-tasa por hora, rate ratio por hora, IC, p-values (Wald/LRT),
    phi de sobre-dispersión y, opcionalmente, TOST de equivalencia práctica.

    se_method:
      - "robust": covarianzas tipo sandwich HC3 (recomendado)
      - "pearson": ajusta escala a Pearson X^2/df (quasi-Poisson)
      - "mle": Poisson puro (solo si no hay sobre-dispersión)
    """
    # -------- higiene de datos --------
    d = df_stats.copy()
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=[count, exposure, time_col])
    d = d[d[exposure] > 0]
    if len(d) < 2:
        return {"status": "insufficient_data", "n_bins": int(len(d))}
    # tiempos → horas desde el primer centro de bin
    t0 = pd.to_datetime(d[time_col]).min()
    th = (pd.to_datetime(d[time_col]) - t0).dt.total_seconds() / 3600.0  # horas
    y = d[count].astype(float).to_numpy()
    off = np.log(d[exposure].astype(float).to_numpy())
    X = sm.add_constant(th.to_numpy())
    # -------- modelo Poisson base --------
    model = sm.GLM(y, X, family=sm.families.Poisson(), offset=off)

    # MLE "puro" (necesario para AIC, deviance y LRT coherentes)
    res_mle = model.fit()
    beta = res_mle.params.copy()
    aic = float(res_mle.aic)
    dev = float(res_mle.deviance)
    pearson_phi = float(res_mle.pearson_chi2 / res_mle.df_resid) if res_mle.df_resid > 0 else np.nan

    # Escoge el método de SE/covarianza para reportar inferencia de beta1
    if se_method == "robust":
        res = model.fit(cov_type="HC3")
    elif se_method == "pearson":
        # Ajusta la escala a Pearson; infla SE si hay sobre-dispersión
        res = model.fit(scale="X2")
    elif se_method == "mle":
        res = res_mle
    else:
        raise ValueError("se_method debe ser 'robust', 'pearson' o 'mle'.")

    # -------- coeficiente de interés --------
    beta1 = float(res.params[1])             # log-rate por hora
    se1   = float(res.bse[1])
    # Wald z y p bilateral
    z = beta1 / se1 if se1 > 0 else np.nan
    p_wald = float(2 * (1 - norm.cdf(abs(z)))) if np.isfinite(z) else np.nan

    # IC (por el método de covarianza elegido)
    ci = res.conf_int(alpha=alpha)  # [[b0_lo,b0_hi],[b1_lo,b1_hi]]
    b1_lo, b1_hi = float(ci[1, 0]), float(ci[1, 1])

    # Efecto interpretable (multiplicador por hora)
    rr_hour = float(np.exp(beta1))
    rr_lo   = float(np.exp(b1_lo))
    rr_hi   = float(np.exp(b1_hi))

    # -------- LRT (deviance) contra modelo sin tendencia --------
    p_lrt = np.nan
    if use_lrt:
        X0 = np.ones((len(y), 1))
        model0 = sm.GLM(y, X0, family=sm.families.Poisson(), offset=off)
        res0 = model0.fit()
        delta_dev = float(res0.deviance - res_mle.deviance)
        # ~ chi^2(1)
        p_lrt = float(1 - chi2.cdf(delta_dev, df=1))

    # -------- Equivalencia práctica (opcional) --------
    tost = None
    if equivalence_rr is not None and equivalence_rr > 1.0:
        delta_log = float(np.log(equivalence_rr))
        tost = tost_equivalence_beta1(beta1, se1, delta_log, alpha=alpha)
        # Para dejar claro el umbral en escala de RR:
        tost["equivalence_rr"] = float(equivalence_rr)

    # -------- (opcional) slope por SD(t) para comparar magnitudes --------
    slope_per_sd = None
    if standardize_time:
        sd_t = float(np.std(th, ddof=0))
        slope_per_sd = float(beta1 * sd_t) if sd_t > 0 else None

    # -------- señalizaciones útiles --------
    suggest_overdisp = bool(pearson_phi > overdispersion_threshold) if np.isfinite(pearson_phi) else False
    note = []
    if suggest_overdisp and se_method == "mle":
        note.append("Sobre-dispersión detectada (phi=%.2f): considera 'robust' o 'pearson'." % pearson_phi)
    if not suggest_overdisp and se_method in ("pearson", "robust"):
        note.append("phi=%.2f sugiere poca sobre-dispersión; MLE también sería válido." % pearson_phi)

    return {
        "status": "ok",
        "n_bins": int(len(y)),
        "se_method": se_method,
        "slope_log_per_hour": beta1,
        "slope_log_per_hour_CI": (b1_lo, b1_hi),
        "rate_ratio_per_hour": rr_hour,
        "rate_ratio_per_hour_CI": (rr_lo, rr_hi),
        "wald_p_two_sided": p_wald,
        "lrt_p": p_lrt,
        "AIC": aic,
        "deviance": dev,
        "dispersion_phi": pearson_phi,
        "suggest_overdispersion": suggest_overdisp,
        "tost_equivalence": tost,
        "slope_log_per_sd_time": slope_per_sd,
        "summary_head": res.summary().as_text()[:1600]  # resumen abreviado para inspección rápida
    }


# ========= Helper para imprimir en una línea legible =========
def format_trend_report(out: dict, time_unit="hora", alpha=0.05):
    if out.get("status") != "ok":
        return f"[trend] Estado: {out.get('status','?')} (n_bins={out.get('n_bins','?')})"
    rr = out["rate_ratio_per_hour"]; lo, hi = out["rate_ratio_per_hour_CI"]
    pW = out["wald_p_two_sided"]; pL = out.get("lrt_p", np.nan)
    phi = out["dispersion_phi"]
    eq = out.get("tost_equivalence")
    eq_str = ""
    if eq is not None:
        eq_str = f" | TOST(rr±): p={eq['p_tost']:.3g}, eq@α={alpha}: {eq['equivalent_at_alpha']}"
    return (f"[{out['se_method']}] RR por {time_unit}={rr:.5f} "
            f"CI{int((1-alpha)*100)}%=({lo:.5f},{hi:.5f}); "
            f"Wald p={pW:.3g}; LRT p={pL:.3g}; phi={phi:.2f}{eq_str}")


def poisson_trend_test(df_stats: pd.DataFrame, x_col: str = "t_mid") -> dict:
    """
    Fit GLM Poisson with log link and offset=log(T). Exog = [1, time_hours].
    Returns slope per hour on log-scale, its p-value, AIC, and textual summary.
    """
    d = df_stats.copy()
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=["N", "T", x_col])
    d = d[(d["T"] > 0)]
    if len(d) < 2:
        return {"slope_per_hour": np.nan, "p_value": np.nan, "AIC": np.nan, "summary": "insufficient data"}

    # Convert time to hours relative to first bin mid
    t0 = pd.to_datetime(d[x_col]).min()
    th = (pd.to_datetime(d[x_col]) - t0).dt.total_seconds() / 3600.0
    y = d["N"].astype(float).to_numpy()
    X = sm.add_constant(th.to_numpy())
    offset = np.log(d["T"].astype(float).to_numpy())
    model = sm.GLM(y, X, family=sm.families.Poisson(), offset=offset)
    res = model.fit(cov_type="HC3")
    params = res.params
    pvals = res.pvalues

    slope_per_hour = float(params[1])
    p_value = float(pvals[1])
    AIC = float(res.aic)
    summ = res.summary2().as_text()
    return {"slope_per_hour": slope_per_hour, "p_value": p_value, "AIC": AIC, "summary": summ}
