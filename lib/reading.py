"""verDAQ log ingestion helpers feeding the probabilistic modeling notebooks."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def pre_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize raw verDAQ exports into analysis-ready numeric columns.

    The Poisson bathtub notebooks expect timestamps as ``datetime64[ns]`` and
    hexadecimal channel readings converted to integers.  This helper performs
    those transformations and forward-fills occasional gaps so downstream
    feature engineering can focus on beam alignment rather than parsing issues.
    """
    # Nans
    mask = df.isna().any(axis=1)
    indices = df.index[mask].tolist()

    df = df.fillna(method='bfill')

    # Aplicación de
    # Conversión del formato de datos
    df['timestamp'] = pd.to_datetime(df['t'], unit='s')

    def safe_hex_to_int(x):
        try:
            return int(x, 16)
        except (ValueError, TypeError):
            return float('nan')

    channel_cols = [col for col in df.columns if col.startswith('ch')]
    df[channel_cols] = df[channel_cols].applymap(safe_hex_to_int)
    return df

def import_file(
    data: str | Path = "../0_raw/verDAQ8_data_2022_05_26_131703_00000.dat",
    log_path: str | Path = "parse_errors.log",
) -> pd.DataFrame:
    """Load a verDAQ text dump and return the cleaned table produced by ``pre_pipeline``."""
    try:
        df = pd.read_csv(
            data,
            delim_whitespace=True,
            comment='#',
            header=None,
            names=["t", "id"] + [f"ch{x}" for x in range(8)],
            on_bad_lines='error'  # Intentamos leer con control
        )
    except pd.errors.ParserError as e:
        # Extraer línea del error
        with open(log_path, 'a') as log:
            log.write(f"Error en archivo: {data}\n")
            log.write(f"{str(e)}\n\n")
        # Volvemos a intentar ignorando las líneas problemáticas
        df = pd.read_csv(
            data,
            delim_whitespace=True,
            comment='#',
            header=None,
            names=["t", "id"] + [f"ch{x}" for x in range(8)],
            on_bad_lines='skip'
        )

    df = pre_pipeline(df)
    return df

