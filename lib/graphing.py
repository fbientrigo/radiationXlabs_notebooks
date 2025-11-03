"""Visualization utilities for aligning beam, DMM, and failure timelines."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

def coincidence_time(time1: pd.Series, time2: pd.Series,
                     data_labels: list = ["Beam", "DMM"],
                     time_index: str = "Time") -> None:
    """
    Grafica los timestamps de dos series de datos y destaca la zona de solape temporal.

    Esta función recibe dos series de timestamps (`time1` y `time2`), las ordena, 
    calcula el intervalo de tiempo en que ambas se solapan y genera un gráfico 
    tipo "event plot" donde:
      - Las marcas verticales representan cada lectura de `time1` (nivel 1) y `time2` (nivel 0).
      - La región de solape aparece sombreada en gris claro.

    Parámetros
    ----------
    time1 : pandas.Series
        Serie de timestamps (datetime64[ns]) correspondientes al primer conjunto de datos.
    time2 : pandas.Series
        Serie de timestamps (datetime64[ns]) correspondientes al segundo conjunto de datos.
    data_labels : list of str, opcional
        Nombres descriptivos para las dos series. `data_labels[0]` etiqueta a `time1`,
        `data_labels[1]` etiqueta a `time2`. Por defecto `["Beam", "DMM"]`.
    time_index : str, opcional
        Nombre de la columna o índice temporal (solo para títulos). Por defecto `"Time"`.

    Devuelve
    -------
    None
        El resultado es una figura mostrada en pantalla; la función no retorna un valor.

    Ejemplos
    --------
    >>> import pandas as pd
    >>> from coincidence_module import coincidence_time
    >>> 
    >>> # Supongamos que tenemos dos DataFrames con columna "Time"
    >>> beam_df = pd.DataFrame({
    ...     "Time": ["2022-05-25 10:09:53.517351680", "2022-05-25 10:10:44.276027648"]
    ... })
    >>> dmm_df = pd.DataFrame({
    ...     "Time": ["2022-05-25 10:10:00.000000000", "2022-05-25 10:12:00.000000000"]
    ... })
    >>> beam_df["Time"] = pd.to_datetime(beam_df["Time"])
    >>> dmm_df["Time"]  = pd.to_datetime(dmm_df["Time"])
    >>> 
    >>> # Llamada a la función para visualizar solape
    >>> coincidence_time(beam_df["Time"], dmm_df["Time"],
    ...                 data_labels=["Beam", "DMM"], time_index="Time")
    >>> # Aparecerá un gráfico con eventplot y zona de solape en gris.

    Notas
    -----
    1. Ambos `time1` y `time2` **deben** ser de tipo datetime64[ns]. Si están como strings,
       primero convertir con `pd.to_datetime()`.
    2. Cada serie se ordena ascendentemente: la función asume que no hay tiempos fuera de orden.
    3. La región sombreada corresponde a:
       ```python
       t_min = max(time1.min(), time2.min())
       t_max = min(time1.max(), time2.max())
       ```
       Cualquier timestamp fuera de [t_min, t_max] queda sin sombrear.
    4. Utiliza `ax.eventplot` para representar cada timestamp como una breve línea horizontal 
       en dos niveles (`y=1` para `time1` y `y=0` para `time2`).
    5. Se recomienda usar `plt.MaxNLocator` y `fig.autofmt_xdate()` para un formateo limpio de fechas.

    """
    # Verificar y asegurar que los objetos sean pandas.Series de datetime
    if not isinstance(time1, pd.Series):
        raise TypeError(f"`time1` debe ser pandas.Series, no {type(time1)}")
    if not isinstance(time2, pd.Series):
        raise TypeError(f"`time2` debe ser pandas.Series, no {type(time2)}")

    # Convertir a datetime64 si no lo están
    if not pd.api.types.is_datetime64_any_dtype(time1):
        time1 = pd.to_datetime(time1)
    if not pd.api.types.is_datetime64_any_dtype(time2):
        time2 = pd.to_datetime(time2)

    # Ordenar ambas series
    time1_sorted = time1.sort_values().reset_index(drop=True)
    time2_sorted = time2.sort_values().reset_index(drop=True)

    # Calcular rango de solape
    t_min = max(time1_sorted.min(), time2_sorted.min())
    t_max = min(time1_sorted.max(), time2_sorted.max())

    # Crear figura y ejes
    fig, ax = plt.subplots(figsize=(10, 3))

    # Sombrar la zona de solape
    ax.axvspan(t_min, t_max, color="lightgrey", alpha=0.5, label="Zona de solape")

    # Graficar cada serie como eventplot en distintos niveles
    ax.eventplot(time1_sorted, lineoffsets=1, linelengths=0.4,
                 colors="tab:blue", label=f"{data_labels[0]} data")
    ax.eventplot(time2_sorted, lineoffsets=0, linelengths=0.4,
                 colors="tab:orange", label=f"{data_labels[1]} data")

    # Etiquetas y formatos
    ax.set_yticks([0, 1])
    ax.set_yticklabels([data_labels[1], data_labels[0]])
    ax.set_xlabel(time_index)
    ax.set_title(f"Timestamps de {data_labels[1]} vs {data_labels[0]} y zona de solape")
    ax.legend(loc="upper right")

    # Formateo de fechas en eje X
    ax.xaxis.set_major_locator(plt.MaxNLocator(6))
    fig.autofmt_xdate(rotation=30)

    # Mostrar gráfico
    plt.show()


def plot_percentile_hist(df: pd.DataFrame,
                         column: str,
                         p_off: float,
                         p_idle_low: float,
                         p_idle_high: float,
                         bins: int = 50,
                         range_hist: tuple = None,
                         figsize: tuple = (12, 4)) -> None:
    """
    Grafica la curva de percentiles y el histograma con zonas sombreadas para una columna numérica.

    Esta función crea dos subplots:
      - Izquierda: curva de percentiles de los datos en `df[column]` de 0 a 100.
      - Derecha: histograma de los valores con escala logarítmica en el eje Y, sombreando tres regiones:
          1. Zona "Off": valores < percentil `p_off`.
          2. Zona "Idle principal": valores entre percentil `p_idle_low` y `p_idle_high`.
          3. Fora de estas zonas, el histograma normal.

    Parámetros
    ----------
    df : pandas.DataFrame
        DataFrame que contiene la columna a analizar.
    column : str
        Nombre de la columna numérica dentro de `df` sobre la cual se calcula percentiles e histograma.
    p_off : float
        Percentil (0–100) que define el límite superior de la zona "Off".
    p_idle_low : float
        Percentil (0–100) que define el límite inferior de la zona "Idle principal".
    p_idle_high : float
        Percentil (0–100) que define el límite superior de la zona "Idle principal".
    bins : int, opcional
        Número de bins para el histograma (por defecto: 50).
    range_hist : tuple (float, float), opcional
        Rango (min, max) de valores para el histograma. Si es None, se usa el rango completo de los datos.
    figsize : tuple, opcional
        Tamaño de la figura en pulgadas (ancho, alto). Por defecto (12, 4).

    Devuelve
    -------
    None
        Muestra la figura con los dos subplots; no retorna valor.

    Raises
    ------
    KeyError
        Si `column` no existe en `df`.
    ValueError
        Si alguno de los percentiles proporcionados no está en el rango [0, 100].

    Ejemplos
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>> # Crear DataFrame de ejemplo
    >>> data = np.random.normal(loc=1.0, scale=0.3, size=1000)
    >>> df_test = pd.DataFrame({"Corriente": data})
    >>> # Graficar percentiles e histograma
    >>> plot_percentile_hist(df_test, column="Corriente",
    ...                      p_off=10, p_idle_low=50, p_idle_high=75,
    ...                      bins=40, range_hist=(0.0, 2.0))
    """

    # 1) Validar existencia de la columna
    if column not in df.columns:
        raise KeyError(f"Columna '{column}' no encontrada en el DataFrame.")

    # 2) Extraer datos y descartar NaN
    data = df[column].dropna().to_numpy()
    if data.size == 0:
        raise ValueError(f"La columna '{column}' no contiene datos válidos (puede estar vacía o solo NaN).")

    # 3) Validar percentiles
    for p in (p_off, p_idle_low, p_idle_high):
        if not (0 <= p <= 100):
            raise ValueError(f"Percentil {p} fuera de rango [0, 100].")

    # 4) Calcular percentiles clave
    pct_off       = np.percentile(data, p_off)
    pct_idle_low  = np.percentile(data, p_idle_low)
    pct_idle_high = np.percentile(data, p_idle_high)

    # 5) Preparar figura con dos subplots
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=figsize, constrained_layout=True)

    # -----------------------------------
    # 5.1) Subplot izquierdo: Curva de percentiles
    # -----------------------------------
    p_vals = np.arange(0, 101, 1)
    pct_vals = np.percentile(data, p_vals)

    ax_left.plot(p_vals, pct_vals, color="tab:blue", linewidth=2)
    ax_left.set_xlabel("Percentil")
    ax_left.set_ylabel(f"{column}")
    ax_left.set_title(f"Curva de Percentiles de '{column}'")
    ax_left.grid(True, linestyle="--", alpha=0.5)

    # Resaltar percentiles de interés
    ax_left.axvline(p_off, color="grey", linestyle="--", alpha=0.7)
    ax_left.text(p_off, pct_off, f"  {p_off}%", va="bottom", color="grey")

    ax_left.axvline(p_idle_low, color="grey", linestyle="--", alpha=0.7)
    ax_left.text(p_idle_low, pct_idle_low, f"  {p_idle_low}%", va="bottom", color="grey")

    ax_left.axvline(p_idle_high, color="grey", linestyle="--", alpha=0.7)
    ax_left.text(p_idle_high, pct_idle_high, f"  {p_idle_high}%", va="bottom", color="grey")

    # -----------------------------------
    # 5.2) Subplot derecho: Histograma con zonas sombreadas
    # -----------------------------------
    # Determinar límite de histograma
    if range_hist is None:
        xmin, xmax = data.min(), data.max()
    else:
        xmin, xmax = range_hist

    # Dibujar histograma
    ax_right.hist(data, bins=bins, range=(xmin, xmax), color="tab:orange", alpha=0.8)
    ax_right.set_yscale("log")
    ax_right.set_xlabel(f"{column}")
    ax_right.set_ylabel("Frecuencia (escala log)")
    ax_right.set_title(f"Histograma de '{column}' con zonas destacadas")
    ax_right.grid(True, linestyle="--", alpha=0.5)

    # Zona "Off": valores < pct_off
    ax_right.axvspan(xmin, pct_off, facecolor="lightgrey", alpha=0.5, label=f"Off (< {p_off}%)")

    # Zona "Idle principal": pct_idle_low ≤ valores ≤ pct_idle_high
    ax_right.axvspan(pct_idle_low, pct_idle_high, facecolor="lightblue", alpha=0.5,
                     label=f"Idle ({p_idle_low}–{p_idle_high}%)")

    # Líneas verticales en los percentiles definidos
    for cut_pct, color in zip([p_off, p_idle_low, p_idle_high], ["grey", "grey", "grey"]):
        cut_val = np.percentile(data, cut_pct)
        ax_right.axvline(cut_val, color=color, linestyle="--", linewidth=1)
        ax_right.text(cut_val, ax_right.get_ylim()[1] * 0.5, f"{cut_pct}%", rotation=90,
                      va="center", ha="right", color=color)

    # Leyenda de zonas
    ax_right.legend(loc="upper right")

    plt.show()


def plot_latchups_on_current(df: pd.DataFrame,
                             eventos_df: pd.DataFrame,
                             current_col: str = "IDC",
                             off_color: str = "red",
                             recovery_color: str = "green",
                             span_alpha: float = 0.2,
                             figsize: tuple = (12, 5)) -> None:
    """
    Grafica la serie temporal de corriente y marca visualmente los eventos de latch-up.

    Para cada evento en `eventos_df` (index como Time_event y columna 'Recuperación_en'),
    dibuja:
      - Una franja sombreada desde Time_event hasta Recuperación_en (alpha=span_alpha).
      - Un marcador rojo en el instante Time_event.
      - Un marcador verde en el instante Recuperación_en.

    Parámetros
    ----------
    df : pandas.DataFrame
        DataFrame indexado por tiempo (datetime64[ns]) que contiene la columna de corriente.
    eventos_df : pandas.DataFrame
        DataFrame de eventos de latch-up, indexado por 'Time_event' y con columna
        'Recuperación_en'.
    current_col : str, opcional
        Nombre de la columna con la corriente (por defecto "IDC").
    off_color : str, opcional
        Color para los marcadores de "off" (por defecto "red").
    recovery_color : str, opcional
        Color para los marcadores de recuperación (por defecto "green").
    span_alpha : float, opcional
        Transparencia de las franjas sombreadas que indican duración de latch-up.
    figsize : tuple, opcional
        Tamaño de la figura (en pulgadas).

    Devuelve
    -------
    None
        Muestra la figura con la serie de corriente y las anotaciones de latch-up.

    Ejemplo de uso
    --------------
    >>> plot_latchups_on_current(df, eventos_df, current_col="IDC")
    """

    # Verificar índices datetime
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        raise ValueError("El índice de `df` debe ser datetime64[ns].")

    if not pd.api.types.is_datetime64_any_dtype(eventos_df.index):
        raise ValueError("El índice de `eventos_df` (Time_event) debe ser datetime64[ns].")

    if "Recuperación_en" not in eventos_df.columns:
        raise KeyError("`eventos_df` debe tener columna 'Recuperación_en'.")

    # Preparar la figura
    fig, ax = plt.subplots(figsize=figsize)

    # Graficar curva de corriente
    ax.plot(df.index, df[current_col], color="tab:blue", linewidth=1, label=current_col)
    ax.set_xlabel("Time")
    ax.set_ylabel(f"{current_col} [A]")
    ax.set_title("Serie de corriente con eventos de latch-up")
    ax.grid(True, linestyle="--", alpha=0.4)

    # Para cada evento, sombrear la duración y marcar puntos
    for t_event, row in eventos_df.iterrows():
        t_recov = row["Recuperación_en"]

        # Sombra desde el evento hasta la recuperación
        ax.axvspan(t_event, t_recov, color="lightgrey", alpha=span_alpha)

        # Marcador rojo en Time_event
        ax.scatter(t_event, row["Off_detectado"], color=off_color, s=30, zorder=5,
                   label="Latch-up" if "Latch-up" not in ax.get_legend_handles_labels()[1] else "")

        # Marcador verde en Recuperación_en
        rec_y = row["IDC_recuperación"]
        ax.scatter(t_recov, rec_y, color=recovery_color, s=30, marker="s", zorder=5,
                   label="Recuperación" if "Recuperación" not in ax.get_legend_handles_labels()[1] else "")

    # Formateo de fechas en eje X
    ax.xaxis.set_major_locator(plt.MaxNLocator(6))
    fig.autofmt_xdate(rotation=30)

    # Leyenda y mostrar
    ax.legend(loc="upper right")
    plt.show()