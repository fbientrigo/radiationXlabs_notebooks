import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import glob
import os
import pandas as pd
import numpy as np

def pre_pipeline(df):
    """
    Limpieza del dataframe y la aplicación de operaciones para dejar los datos en el formato más comodo
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

def import_file(data="../0_raw/verDAQ8_data_2022_05_26_131703_00000.dat", log_path="parse_errors.log"):
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

