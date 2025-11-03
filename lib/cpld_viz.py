"""Visualization helpers for CPLD counters used in the Poisson bathtub studies."""

from __future__ import annotations

from typing import List, Optional, Sequence

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

__all__ = [
    "plot_bit_rate_heatmap",
    "plot_bit_timeseries",
]


def _resolve_bit_columns(df: pd.DataFrame, prefix: str) -> List[str]:
    columns = [col for col in df.columns if col.startswith(prefix) and col[len(prefix) :].isdigit()]
    return sorted(columns, key=lambda name: int(name[len(prefix) :]))


def plot_bit_rate_heatmap(
    df: pd.DataFrame,
    time_col: str = "time",
    bit_prefix: str = "bitn",
    freq: str | pd.Timedelta = "1H",
    cmap: str = "mako",
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """Representa un mapa de calor con la tasa de bit flips por intervalo.

    Los contadores ``bitn*`` son acumulativos, por lo que primero se calculan las
    diferencias positivas (incrementos) y posteriormente se acumulan en ventanas
    temporales definidas por ``freq``.  El resultado final se normaliza en
    eventos por hora.

    Parámetros
    ----------
    df:
        DataFrame con los contadores generados por
        :func:`lib.cpld_decode.compute_counters`.
    time_col:
        Nombre de la columna temporal.
    bit_prefix:
        Prefijo que identifica las columnas por bit (por defecto ``"bitn"``).
    freq:
        Ventana de resampleo (por ejemplo ``"15min"``, ``"1H"``...).
    cmap:
        Paleta utilizada por :func:`seaborn.heatmap`.
    ax:
        Eje de Matplotlib opcional.  Si no se proporciona se crea una figura
        nueva.

    Devuelve
    -------
    matplotlib.axes.Axes
        Eje con el mapa de calor dibujado.

    Ejemplos
    --------
    >>> ax = plot_bit_rate_heatmap(processed_df, freq="30min")
    >>> ax.set_title("Tasa de eventos por bit")
    """

    if time_col not in df.columns:
        raise KeyError(f"La columna temporal '{time_col}' no está presente en el DataFrame.")

    bit_columns = _resolve_bit_columns(df, bit_prefix)
    if not bit_columns:
        raise ValueError(f"No se encontraron columnas que empiecen por '{bit_prefix}'.")

    time_index = pd.to_datetime(df[time_col])
    counts = df[bit_columns].apply(pd.to_numeric, errors="coerce").ffill().fillna(0)
    increments = counts.diff().clip(lower=0).fillna(0)

    increments.index = pd.DatetimeIndex(time_index)
    increments = increments.sort_index()

    if isinstance(freq, pd.Timedelta):
        window = freq
        rule = pd.tseries.frequencies.to_offset(freq)
    else:
        window = pd.to_timedelta(freq)
        rule = freq

    if window.total_seconds() == 0:
        raise ValueError("La ventana de resampleo debe ser mayor que cero.")

    aggregated = increments.resample(rule).sum()
    per_hour = aggregated / (window.total_seconds() / 3600.0)

    data = per_hour.rename(columns=lambda c: int(c[len(bit_prefix) :]))
    data = data.sort_index(axis=1)

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))

    sns.heatmap(
        data.T,
        cmap=cmap,
        ax=ax,
        cbar_kws={"label": "Eventos por hora"},
    )
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Bit")
    ax.set_title("Tasa de bit flips por intervalo")
    return ax


def plot_bit_timeseries(
    df: pd.DataFrame,
    bits: Optional[Sequence[int]] = None,
    time_col: str = "time",
    bit_prefix: str = "bitn",
    events: Optional[pd.DataFrame] = None,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """Dibuja la evolución temporal de los contadores acumulativos.

    Parámetros
    ----------
    df:
        DataFrame con columnas ``bitn*``.
    bits:
        Lista de bits a representar.  Si es ``None`` se seleccionan automáticamente
        los cuatro primeros disponibles.
    time_col:
        Columna temporal.
    bit_prefix:
        Prefijo de las columnas por bit.
    events:
        Tabla generada por :func:`detect_bit_increments`.  Si se facilita se
        marcan los eventos sobre la gráfica.
    ax:
        Eje opcional de Matplotlib.

    Devuelve
    -------
    matplotlib.axes.Axes
        Eje con la serie temporal.

    Ejemplos
    --------
    >>> ax = plot_bit_timeseries(processed_df, bits=[0, 1, 2])
    >>> ax.set_ylabel("Eventos acumulados")
    """

    if time_col not in df.columns:
        raise KeyError(f"La columna temporal '{time_col}' no está presente en el DataFrame.")

    bit_columns = _resolve_bit_columns(df, bit_prefix)
    if not bit_columns:
        raise ValueError(f"No se encontraron columnas que empiecen por '{bit_prefix}'.")

    available_bits = [int(col[len(bit_prefix) :]) for col in bit_columns]
    available_bits.sort()

    if bits is None:
        bits = available_bits[:4]
    else:
        missing = set(bits) - set(available_bits)
        if missing:
            raise KeyError(f"Los bits {sorted(missing)} no están presentes en el DataFrame.")

    time_values = pd.to_datetime(df[time_col])

    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))

    palette = sns.color_palette(n_colors=len(bits))
    color_map = dict(zip(bits, palette))

    for bit in bits:
        series = pd.to_numeric(df[f"{bit_prefix}{bit}"], errors="coerce").ffill().fillna(0)
        ax.plot(time_values, series, label=f"bit {bit}", color=color_map[bit])

    if events is not None and not events.empty:
        event_df = events[events["bit"].isin(bits)].copy()
        if time_col in event_df.columns:
            added_labels: set[str] = set()
            for bit in bits:
                subset = event_df[event_df["bit"] == bit]
                if subset.empty:
                    continue
                label = f"Eventos bit {bit}"
                plot_label = label if label not in added_labels else ""
                ax.scatter(
                    subset[time_col],
                    subset["count"],
                    color=color_map[bit],
                    edgecolor="white",
                    zorder=5,
                    label=plot_label,
                )
                added_labels.add(label)

    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Eventos acumulados")
    ax.set_title("Evolución de bit flips")
    handles, labels = ax.get_legend_handles_labels()
    unique = {label: handle for handle, label in zip(handles, labels) if label}
    if unique:
        ax.legend(list(unique.values()), list(unique.keys()), loc="best")
    ax.grid(True, linestyle="--", alpha=0.3)
    return ax
