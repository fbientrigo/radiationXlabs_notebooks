import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

# Función para cargar un solo CSV, asignar run_group, verificar monotonía y graficar
def read_beam_data(path: str,
                       run_id: int,
                       plot: bool = False,
                       title: str | None = None) -> pd.DataFrame:
    """
    Load a single Beam CSV, assign a run group, check for monotonicity, and optionally plot key variables.

    Parameters
    ----------
    path : str
        Filesystem path to the Beam CSV file. The CSV must contain the columns
        "time", "TID_RAW1", "HEH", and "N1MeV_RAW0".
    run_id : int
        Identifier to assign to the `run_group` column for this data segment.
    plot : bool, default=False
        If True, generate a two-panel figure:
          - Left panel: histogram of timestamp sampling.
          - Right panel: log-scaled time series of TID, HEH, and N1MeV.
    title : str or None, default=None
        Optional super-title for the figure (only used if `plot=True`).

    Returns
    -------
    pd.DataFrame
        A DataFrame with columns:
          - `time` (datetime64[ns])
          - `TID` (float)
          - `HEH` (float)
          - `N1MeV` (float)
          - `run_group` (int)
        Sorted by `time` and with monotonicity verified for TID, HEH, and N1MeV.

    Notes
    -----
    - If any of TID, HEH, or N1MeV is not strictly non-decreasing, an error message
      is printed but execution continues.
    - time is parsed via `pd.to_datetime`, and the DataFrame is reset_index(drop=True)
      after sorting.

    Examples
    --------
    >>> df = read_my_beam("beam_run1.csv", run_id=1, plot=True, title="Run 1 Overview")
    """
    import pandas as pd
    import matplotlib.pyplot as plt

    # 1) Leer y renombrar columnas
    df_run = pd.read_csv(path, usecols=["Time", "TID_RAW1", "HEH", "N1MeV_RAW0"])
    df_run["time"] = pd.to_datetime(df_run["Time"])
    df_run = df_run.rename(columns={"TID_RAW1": "TID", "N1MeV_RAW0": "N1MeV"})
    df_run = df_run[["time", "TID", "HEH", "N1MeV"]].sort_values("time").reset_index(drop=True)

    # 2) Asignar identificador de run
        # Utilizado a modo de organizar los casos de tener datos de beam separados por mucho
    df_run["run_group"] = int(run_id)

    # 3) Verificar monotonía sin interrumpir la ejecución
    if not df_run["TID"].is_monotonic_increasing:
        print(f"ERROR: TID no es monotónico en {path}")
    if not df_run["HEH"].is_monotonic_increasing:
        print(f"ERROR: HEH no es monotónico en {path}")
    if not df_run["N1MeV"].is_monotonic_increasing:
        print(f"ERROR: N1MeV no es monotónico en {path}")

    # 4) Gráficos si plot=True
    if plot:
        # Preparar figura con 1 fila, 2 columnas
        fig, (ax_time, ax_vars) = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)

        # ---- Izquierda: histograma de los timestamps (frecuencia de lecturas en el tiempo) ----
        ax_time.hist(df_run["time"].values.astype("datetime64[s]"), bins=50, color="tab:blue", alpha=0.7)
        ax_time.set_title(f"Distribución de time\n{os.path.basename(path)}")
        ax_time.set_xlabel("time")
        ax_time.set_ylabel("Frecuencia")
        for tl in ax_time.get_xticklabels():
            tl.set_rotation(30)

        # ---- Derecha: TID, HEH y N1MeV vs time (escala log en Y) ----
        ax_vars.plot(df_run["time"], df_run["TID"],   label="TID",   linewidth=1)
        ax_vars.plot(df_run["time"], df_run["HEH"],   label="HEH",   linewidth=1)
        ax_vars.plot(df_run["time"], df_run["N1MeV"], label="N1MeV", linewidth=1)
        ax_vars.set_yscale("log")
        ax_vars.set_title(f"Contadores vs time\n{os.path.basename(path)}")
        ax_vars.set_xlabel("time")
        ax_vars.set_ylabel("Valor (escala log)")
        ax_vars.legend(loc="upper left")
        for tl in ax_vars.get_xticklabels():
            tl.set_rotation(30)

        # aqui poner el titulo a la figura completa
        if title:
            # Ajusta 'y' para que el título no choque con los subplots
            fig.suptitle(title, fontsize=14, y=1.1)

        plt.show()


    return df_run

def beam_pipeline(df: pd.DataFrame,
                  epsilon: float = 1e-7,
                  debug: bool = False, debug_plot: bool = False) -> pd.DataFrame:
    """
    Compute differential dose rates for Beam data and flag beam-on periods.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame with columns:
          - `time` (datetime64[ns])
          - `TID` (float)
          - `HEH` (float)
          - `N1MeV` (float)
    epsilon : float, default=1e-7
        Threshold dose rate [Gy/s] above which the beam is considered "on".
        Typical ambient background is on the order of 1e-7 Gy/s.
    debug : bool, default=False
        If True, print summary statistics:
          - Percentage of time beam is on.
          - Mean hadron flux (HEH_on / T_on) [1/s].
          - Mean neutron flux (N1MeV_on / T_on) [1/s].

    Returns
    -------
    pd.DataFrame
        The original DataFrame augmented with the following columns:
          - `dt` : float, time difference in seconds between successive samples.
          - `dTID`, `dHEH`, `dN1MeV` : float, first differences of the counters.
          - `TID_dose_rate`, `HEH_dose_rate`, `N1MeV_dose_rate` : float, differential
            counters divided by `dt`.
          - `beam_on` : bool, True where `TID_dose_rate` > `epsilon`.

    Examples
    --------
    >>> df2 = beam_pipeline(df)
    >>> # Inspect periods where beam was on
    >>> df2[df2['beam_on']].head()
    """
    # df con columnas time, TID, HEH, N1MeV
    df = df.sort_values('time')
    df['dt']        = df['time'].diff().dt.total_seconds()
    df['dTID']      = df['TID'].diff()
    df['dHEH']      = df['HEH'].diff()
    df['dN1MeV']    = df['N1MeV'].diff()
    df['TID_dose_rate'] = df['dTID'] / df['dt']
    df['N1MeV_dose_rate'] = df['dN1MeV'] / df['dt']
    df['HEH_dose_rate'] = df['dHEH'] / df['dt']
    
    df['beam_on'] = df['TID_dose_rate'] > epsilon

    # filtra periodos on
    on = df[df['beam_on']]

    # total tiempo on y conteos on
    T_on       = on['dt'].sum()
    HEH_on     = on['dHEH'].sum()
    N1MeV_on   = on['dN1MeV'].sum()

    if debug:
            # porcentaje ON
        percentage_on = (df['TID_dose_rate'] > epsilon).mean()
        print("Percentage of Beam ON", percentage_on)
        # flujos medios
        flux_HEH   = HEH_on   / T_on   # hadrones/s
        flux_N1MeV = N1MeV_on / T_on   # neutrones/s

        print(flux_HEH, "hadrons/sec")
        print(flux_N1MeV, "neutrons/sec")

    if debug_plot:
        import seaborn as sns
        import matplotlib.pyplot as plt

        # 1. Dibujar el boxplot
        sns.boxplot(y=df['TID_dose_rate'])

        # 2. Escala logarítmica en el eje Y
        plt.yscale('log')

        # 3. Añadir línea horizontal en y = 1e-6, roja y punteada
        plt.axhline(
            y=epsilon,
            color='red',
            linestyle=':',   # ':' es línea punteada
            linewidth=1.5    # grosor de línea
        )

        # 4. Mostrar la gráfica
        plt.show()


    return df