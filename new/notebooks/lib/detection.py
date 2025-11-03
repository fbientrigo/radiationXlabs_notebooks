import numpy as np
import pandas as pd

def detect_latchups(df: pd.DataFrame,
                    current_col: str,
                    off_threshold: float,
                    idle_low: float,
                    idle_high: float) -> pd.DataFrame:
    """
    Detecta transiciones 'idle principal → off' en una serie de corriente DC.

    Esta función recorre la columna `current_col` de `df`, asumiendo que el índice
    de `df` es de tipo datetime64[ns], y detecta los momentos en que la corriente
    cae desde un valor dentro del rango [idle_low, idle_high] hasta un valor menor
    que off_threshold. Para cada evento, también busca el siguiente instante en que
    la corriente vuelve a ser ≥ idle_low para medir la duración del apagado.

    Parámetros
    ----------
    df : pandas.DataFrame
        DataFrame indexado por tiempo (datetime64[ns]) que contiene la serie de corriente.
    current_col : str
        Nombre de la columna en `df` que almacena la corriente (valores float).
    off_threshold : float
        Valor umbral (en las mismas unidades que `current_col`) por debajo del cual se
        considera que el dispositivo está "off" (latch-up detectado).
    idle_low : float
        Límite inferior (inclusive) del rango de "idle principal" (corriente normal antes
        de un latch-up).
    idle_high : float
        Límite superior (inclusive) del rango de "idle principal".

    Retorna
    -------
    eventos_df : pandas.DataFrame
        DataFrame con un registro por cada evento 'idle → off'. Las columnas son:
          - Time_event (datetime64[ns]): instante en que la corriente cae por debajo de off_threshold.
          - Duración_s (int): tiempo (en segundos) hasta que la corriente vuelve ≥ idle_low.
          - Idle_previo (float): valor de corriente justo antes de la caída.
          - Off_detectado (float): valor de corriente en el momento de la caída (< off_threshold).
          - Recuperación_en (datetime64[ns]): primer instante en que la corriente ≥ idle_low.
          - IDC_recuperación (float): valor de corriente en el momento de recuperación.

    Raises
    ------
    KeyError
        Si `current_col` no existe en `df`.
    ValueError
        Si el índice de `df` no es de tipo datetime64[ns] o si `df[current_col]` no es numérico.

    Ejemplos
    --------
    >>> import pandas as pd
    >>> data = {
    ...     "Time": ["2022-06-01 12:00:00", "2022-06-01 12:00:04", "2022-06-01 12:00:08",
    ...              "2022-06-01 12:00:12", "2022-06-01 12:00:16", "2022-06-01 12:00:20"],
    ...     "IDC": [1.25, 1.23, 0.005, 0.003, 1.22, 1.26]
    ... }
    >>> df_test = pd.DataFrame(data)
    >>> df_test["Time"] = pd.to_datetime(df_test["Time"])
    >>> df_test = df_test.set_index("Time")
    >>> eventos = detect_latchups(df_test, current_col="IDC",
    ...                           off_threshold=0.01, idle_low=1.20, idle_high=1.30)
    >>> print(eventos)
                      Time_event  Duración_s  Idle_previo  Off_detectado  \
    0 2022-06-01 12:00:04           8         1.23          0.005   

               Recuperación_en  IDC_recuperación  
    0 2022-06-01 12:00:12            1.22  

    """

    # Validar existencia de la columna de corriente
    if current_col not in df.columns:
        raise KeyError(f"Columna '{current_col}' no encontrada en el DataFrame.")

    # Validar que el índice sea datetime64[ns]
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        raise ValueError("El índice de `df` debe ser de tipo datetime64[ns].")

    # Validar que la columna de corriente sea numérica
    if not pd.api.types.is_numeric_dtype(df[current_col]):
        raise ValueError(f"La columna '{current_col}' debe contener valores numéricos.")

    # Extraer los valores de corriente y los timestamps a arrays
    idc_arr = df[current_col].values
    times = df.index.to_numpy()

    events = []
    prev_idle = False

    # Recorrer todas las muestras a partir de la segunda
    for i in range(1, len(idc_arr)):
        prev = idc_arr[i - 1]
        curr = idc_arr[i]
        t = times[i]

        # Marcar si la muestra previa está en “idle principal”
        prev_idle = (idle_low <= prev <= idle_high)

        # Si cayó de “idle principal” a por debajo de off_threshold
        if prev_idle and (curr < off_threshold):
            # Buscar índice de recuperación: primer valor ≥ idle_low en i+1:
            resto_idx = np.where(idc_arr[i+1:] >= idle_low)[0]
            if resto_idx.size > 0:
                j = resto_idx[0] + (i + 1)
                t_rec = times[j]
                duration_s = (t_rec - t).astype("timedelta64[s]").astype(int)
                events.append({
                    "Time_event":        t,
                    "Duración_s":        duration_s,
                    "Idle_previo":       prev,
                    "Off_detectado":     curr,
                    "Recuperación_en":   t_rec,
                    "IDC_recuperación":  idc_arr[j]
                })

    # Si no se detectó ningún evento, retornar DataFrame vacío con columnas
    cols = ["Time_event", "Duración_s", "Idle_previo", "Off_detectado",
            "Recuperación_en", "IDC_recuperación"]
    if not events:
        return pd.DataFrame(columns=cols)

    # Convertir lista de eventos en DataFrame y regresar
    eventos_df = pd.DataFrame(events).set_index("Time_event")
    return eventos_df


def running_diff(df, global_dt):
    """
    Context: Measuring difference in time-stamp between a uniform sampling and batch sampling
    gets the difference at the difference points
    """
    timestamps = df['timestamp'].values.astype('datetime64[ns]')
    n = np.arange(len(timestamps))
    t0 = timestamps[0]

    predicted_timestamps = t0 + n * np.timedelta64(int(global_dt * 1e9), 'ns')
    running_dif = (predicted_timestamps - timestamps) / np.timedelta64(1, 's')  # en segundos

    return running_dif
