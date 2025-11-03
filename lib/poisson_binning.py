"""Deprecated compatibility wrappers for legacy poisson_binning helpers.

Use :mod:`radbin.core` and :mod:`radbin.glm` directly for new development.
"""
from __future__ import annotations

import warnings
from typing import List, Sequence, Tuple

import pandas as pd

from radbin import core as _core
from radbin import glm as _glm

__all__ = [
    "to_datetime_smart",
    "compute_scaled_time_clipped",
    "extract_event_times",
    "detect_resets",
    "build_bins_by_resets",
    "build_bins_reset_locked",
    "build_bins_equal_fluence",
    "build_bins_equal_count",
    "garwood_rate_ci",
    "summarize_bins",
    "build_and_summarize",
    "inspect_scaled_time",
    "check_real_output",
    "conservation_checks",
    "recommend_k_multiple",
    "bin_and_rate",
    "fit_poisson_trend",
    "poisson_trend_test_plus",
    "poisson_trend_test",
    "format_trend_report",
]

warnings.warn(
    "lib.poisson_binning is deprecated; use radbin.core and radbin.glm instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export the tested implementations from radbin as the single source of truth.
to_datetime_smart = _core.to_datetime_smart
compute_scaled_time_clipped = _core.compute_scaled_time_clipped
extract_event_times = _core.extract_event_times
detect_resets = _core.detect_resets
build_bins_reset_locked = _core.build_bins_reset_locked
build_bins_equal_fluence = _core.build_bins_equal_fluence
build_bins_equal_count = _core.build_bins_equal_count
garwood_rate_ci = _core.garwood_rate_ci
summarize_bins = _core.summarize_bins
build_and_summarize = _core.build_and_summarize
inspect_scaled_time = _core.inspect_scaled_time
check_real_output = _core.check_real_output
conservation_checks = _core.conservation_checks
recommend_k_multiple = _core.recommend_k_multiple
poisson_trend_test_plus = _glm.poisson_trend_test_plus
poisson_trend_test = _glm.poisson_trend_test
format_trend_report = _glm.format_trend_report


def build_bins_by_resets(
    reset_table: Sequence,
    k_multiple: int = 1,
) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    """Compatibility wrapper around :func:`radbin.core.build_bins_reset_locked`."""
    warnings.warn(
        "build_bins_by_resets is deprecated; use radbin.core.build_bins_reset_locked instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if isinstance(reset_table, pd.DataFrame):
        resets = pd.to_datetime(reset_table.get("time", []))
    else:
        resets = pd.to_datetime(pd.Index(list(reset_table)))
    edges = _core.build_bins_reset_locked(list(resets), k_multiple=k_multiple)
    return [(edges[i], edges[i + 1]) for i in range(max(len(edges) - 1, 0))]


def bin_and_rate(
    df_beam: pd.DataFrame,
    df_fails: pd.DataFrame,
    n_subsystems: int,
    flux_col: str = "N1MeV_dose_rate",
    beam_on_col: str = "beam_on",
    k_multiple: int = 1,
    min_separation: float = 0.0,
    ref_flux: float | None = None,
    alpha: float = 0.05,
    **kwargs,
) -> pd.DataFrame:
    """Deprecated wrapper that delegates to :func:`radbin.core.build_and_summarize`."""
    warnings.warn(
        "bin_and_rate is deprecated; use radbin.core.build_and_summarize instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    _ = (beam_on_col, min_separation, ref_flux)  # legacy parameters are ignored
    return _core.build_and_summarize(
        df_beam,
        df_fails,
        bin_mode="reset",
        k_multiple=k_multiple,
        flux_col=flux_col,
        alpha=alpha,
        T_source="beam",
        **{k: v for k, v in kwargs.items() if k in {"area_norm", "min_events_per_bin", "min_exposure_per_bin"}},
    )


def fit_poisson_trend(
    bins_df: pd.DataFrame,
    use_eq_time: bool = True,
    alpha: float = 0.05,
    **kwargs,
):
    """Deprecated wrapper that delegates to :func:`radbin.glm.poisson_trend_test_plus`."""
    warnings.warn(
        "fit_poisson_trend is deprecated; use radbin.glm.poisson_trend_test_plus instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    count_col = "N" if "N" in bins_df.columns else "k"
    if use_eq_time:
        exposure_candidates = ["T", "eq_time_exp_per_sub", "eq_time_exposure"]
    else:
        exposure_candidates = ["width_s", "time_exp_per_sub", "time_exposure"]
    exposure_col = next((c for c in exposure_candidates if c in bins_df.columns), None)
    if exposure_col is None:
        raise ValueError("Could not determine exposure column for legacy trend data.")
    return _glm.poisson_trend_test_plus(
        bins_df,
        count=count_col,
        exposure=exposure_col,
        time_col="t_mid",
        alpha=alpha,
        **kwargs,
    )
