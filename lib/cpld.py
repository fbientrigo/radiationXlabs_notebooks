import glob
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

import logging
from typing import List, Dict, Tuple, Union, Optional

import time
import numpy as np
import re

def parse_message(raw: str) -> tuple[datetime, int, str, str]:
    """
    Parse a raw CPLD data line into its constituent fields.

    This function normalizes the raw string by stripping unwanted characters,
    splits on commas, validates field lengths, and converts the UNIX timestamp
    into a Python datetime.

    Parameters
    ----------
    raw : str
        A raw line from the CPLD data file, e.g. "*1653423316.2195077 #525#1E8, A5C3".

    Returns
    -------
    time : datetime.datetime
        The timestamp of the message in UTC+2.
    lfsr : int
        The LFSR register value parsed from the second field.
    b0 : str
        The first 4-digit hex payload from the third field.
    b1 : str
        The second 4-digit hex payload from the fourth field.

    Raises
    ------
    ValueError
        If the line does not split into at least four parts, or if the
        third or fourth parts are not exactly four hex digits.

    Examples
    --------
    >>> parse_message("1653423316.2195077,525,A5C3,4B2F")
    (datetime.datetime(2022, 5, 24, 12, 35, 16, 219508), 525, 'A5C3', '4B2F')
    """
    line = raw.replace('*', '').replace(' #', ',').strip()
    parts = line.split(',')
    if len(parts) < 4 or len(parts[2]) != 4 or len(parts[3]) != 4:
        raise ValueError("Formato inválido")
    ts = float(parts[0])
    time = datetime.utcfromtimestamp(ts) + timedelta(hours=2)
    lfsr = int(parts[1])
    b0, b1 = parts[2], parts[3]
    return time, lfsr, b0, b1


def count_fails(hex_str: str) -> int:
    """
    Count the number of failure bits in the upper byte of a hex string.

    Converts the input hex string to an integer, inverts and masks to extract
    the high byte, then counts the number of bits set to 1 in that byte.

    Parameters
    ----------
    hex_str : str
        A 4-character hexadecimal string, e.g. "A5C3".

    Returns
    -------
    int
        Number of bits set to 1 in the inverted high byte (0–8). Returns 0
        if the input is invalid.

    Notes
    -----
    - Uses mask 0xFF00 to isolate the high byte after inversion.
    - Intended to count “error” bits in the CPLD status word.

    Examples
    --------
    >>> count_fails("FF00")
    0
    >>> count_fails("00FF")
    8
    """

    try:
        val = int(hex_str, 16)
        masked = (~val & 0xFF00) >> 8
        # Conteo de bits
        return bin(masked).count('1')
    except ValueError:
        return 0  # En caso de error de parseo
    


def nfails(k: int, nbits: int = 16) -> int:
    """
    Count the number of 1-bits in the lowest `nbits` bits of an integer.

    This is a generalized popcount over the specified bit-width.

    Parameters
    ----------
    k : int
        Integer whose bits are to be counted.
    nbits : int, default=16
        Number of least significant bits to consider.

    Returns
    -------
    int
        Total count of bits set to 1 within the lowest `nbits` bits of `k`.

    Examples
    --------
    >>> nfails(0xFFFF, nbits=16)
    16
    >>> nfails(0b101010, nbits=6)
    3
    """
    return sum(
        (k >> i) & 1 for i in range(nbits)
        )

def load_and_clean_text(filenames: List[str],
                        replacements: List[Tuple[str, str]]) -> List[str]:
    """
    Lee todos los archivos, aplica reemplazos y devuelve una lista de líneas limpias.
    """
    lines: List[str] = []
    for fn in filenames:
        raw = open(fn, 'r', encoding='utf-8', errors='ignore').read()
        for old, new in replacements:
            raw = raw.replace(old, new)
        lines.extend(raw.splitlines())
    return lines


def parse_line_generic(
    raw: str,
    ts_threshold: datetime
    ) -> Tuple[
        Optional[datetime],    # time: datetime si se parsea OK, o None
        Optional[int],         # lfsr: int si OK, o None
        Dict[str, str],        # bytes_dict: { 'B0': 'FF00', … } si OK, o {}
        bool                   # valid: True si toda la línea es válida
    ]:
    """
    Parseo genérico de una línea CPLD.
    - raw: línea ya limpia (reemplazos aplicados).
    - ts_threshold: fecha mínima aceptada.
    Returns: (time, lfsr, dict_bytes, valid)
    """
    HEX_PATTERN = re.compile(r'^[0-9A-Fa-f]{4}$')

    parts = [p.strip() for p in raw.split(',')]
    # 1) Timestamp
    try:
        ts = float(parts[0])
        time = datetime.utcfromtimestamp(ts) + timedelta(hours=2)
    except Exception:
        return None, None, {}, False

    # 2) LFSR
    try:
        lfsr = int(parts[1])
    except Exception:
        return time, None, {}, False

    # 3) Extracción dinámica de bytes
    b_values = parts[2:]
    # 4) Validación de cada byte con regex
    if not b_values or any(not HEX_PATTERN.match(b) for b in b_values):
        return time, lfsr, {}, False

    # 5) Filtrado por fecha mínima
    if time < ts_threshold:
        return None, None, {}, False

    # 6) Construcción del diccionario de bytes
    bytes_dict = {f'B{i}': b for i, b in enumerate(b_values)}
    if len(bytes_dict) > 4: # no deberian haber más datos, así que estamos recibiendo lineas corruptas, mezcladas
        return time, lfsr, {}, False

    return time, lfsr, bytes_dict, True


def read_cpld_data(cpld_path: str,
                   replacements: Union[Dict[str,str], List[Tuple[str,str]]] = None,
                   debug: bool = False,
                   get_detailed_errors: bool = False
                  ) -> Union[Tuple[pd.DataFrame, pd.DataFrame],
                             Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    """
    Read and parse a series of CPLD data files into structured DataFrames.
    Given that we have multiplecolumns or one

    Iterates over all files matching `cpld_path`, applies line-by-line parsing,
    and categorizes valid versus invalid records. Invalid lines can be
    optionally aggregated by day and hour.

    Parameters
    ----------
    cpld_path : str, default='../0_raw/Campaign3/cpld/run/cpld_data_*.dat'
        Glob pattern for CPLD data files.
    replacements : list of (old, new) or dict {old: new}, optional
        Repalcement rules applied in order, for the raw content before parsing
        Example: [('*',''), (' #',',')] o {'*':'', ' #':','}
    debug : bool, default=False
        If True, print summary statistics of parsing (counts of valid/invalid lines).
    get_detailed_errors : bool, default=False
        If True, return per-hour error counts alongside data; otherwise return
        only the parsed and bad-records DataFrames.

    Returns
    -------
    df : pandas.DataFrame
        Parsed records with columns ['time', 'lfsrTMR', 'B0', 'B1'], sorted by time.
    df_bad : pandas.DataFrame
        Timestamps of lines that failed parsing but passed a minimum-date filter.
    errors : pandas.DataFrame, optional
        If `get_detailed_errors=True`, a DataFrame of bad-line counts per hour.

    Notes
    -----
    - Lines with unparsable timestamps prior to 2022-01-01 are dropped silently.
    - Valid lines are those where `parse_message` succeeds.
    - Bad records are those where parsing fails but timestamp ≥ 2022-01-01.

    Examples
    --------
    >>> df, df_bad = read_my_cpld(debug=True)
    >>> df.head()
    >>> df_bad['date'].value_counts()
    """
    fnames = glob.glob(cpld_path)

    ts_threshold = datetime(2022, 1, 1) # threshold, no tendría sentido datos previo a esto
    records = []
    bad_records = []
    bad_count = 0
    drops_invalid_ts = 0
    last_ts = None

    # Preparar paths y reemplazos
    filenames = glob.glob(cpld_path)
    if isinstance(replacements, dict):
        replacements = list(replacements.items())
    replacements = replacements or [('*',''), (' #',',')]

    #---

    lines = load_and_clean_text(filenames, replacements)
    last_valid_time = None
    for raw in lines:
        time, lfsr, bs_dict, valid = parse_line_generic(raw, ts_threshold)
        if valid and time and lfsr is not None and bs_dict:
            last_valid_time = time
            record = {'time': time, 'lfsrTMR': lfsr, **bs_dict}
            records.append(record)
        else:
            # registrar error con último timestamp válido
            if last_valid_time:
                bad_records.append({'ts': last_valid_time})

    # DataFrame de registros válidos
    df = pd.DataFrame(records).sort_values('time').reset_index(drop=True)

    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    # DataFrame de bad records
    df_bad = pd.DataFrame(bad_records)
    if not df_bad.empty:
        df_bad['date'] = df_bad['ts'].dt.date
        df_bad['hour'] = df_bad['ts'].dt.floor('h')

    if debug:
        logger.info(f"  Registros válidos: {len(df)}")
        logger.info(f"  Registros inválidos: {len(df_bad)}")

    if get_detailed_errors and not df_bad.empty:
        errors_hora = df_bad.groupby('hour').size().reset_index(name='bad_lines')
        return df, df_bad, errors_hora
    else:
        return df, df_bad



# ========================== PIPELINE =================================
def cpld_pipeline(df: pd.DataFrame, debug: bool = False):
    """
    Analyze CPLD binary status streams to extract failure and periodicity metrics.

    Processes a DataFrame of raw hex fields 'B0' and 'B1', filters valid rows,
    unpacks bits, computes per-sample failure counts, detects resets, and
    accumulates both instantaneous and periodic failure statistics.

    Parameters
    ----------
    df : pandas.DataFrame
        Input with columns ['time', 'lfsrTMR', 'B0', 'B1'].
    debug : bool, default=False
        If True, print timing and shape information for each processing step.

    Returns
    -------
    df_valid : pandas.DataFrame
        Original DataFrame augmented with:
          - fails_inst : int — failures per sample
          - fails_acum : int — bias-corrected cumulative failures
          - bitn0..bitn15 : int — cumulative rising-edge counts per bit
          - bitnP0..bitnP15 : int — cumulative periodic event counts per bit
    edges_and_resets : tuple (edges: np.ndarray, resets: np.ndarray)
        Boolean arrays indicating all rising edges and reset points.
    edges_up_down : tuple (edges_up: np.ndarray, edges_dn: np.ndarray)
        Arrays for individual bit rising and falling transitions.
    bit_periodic : np.ndarray
        Periodic-event counts by sample and bit, shape (n_samples, 16).

    Notes
    -----
    - Uses `np.unpackbits` to vectorize bit extraction of the high byte.
    - A “reset” is defined as a zero‐fail sample following any positive‐fail sample.
    - Periodic counts are derived from cumulative falling-edge episodes.

    Examples
    --------
    >>> df_out, (edges, resets), (up, dn), periodic = cpld_pipeline(df, debug=True)
    >>> df_out.filter(regex='fails|bitn').head()
    """
    # 1) Identificar columnas de bytes dinámicamente
    byte_cols = sorted(
        [col for col in df.columns if col.startswith('B')],
        key=lambda x: int(x[1:])  # ordena por índice numérico
    )

    # 2) Filtrar filas con hex válidos en todas las columnas B*
    hex_pat = re.compile(r'^[0-9A-Fa-f]{4}$')
    valid_mask = df[byte_cols].astype(str).apply(
        lambda col: col.str.fullmatch(hex_pat.pattern)
    ).all(axis=1)
    df_valid = df[valid_mask].reset_index(drop=True)
    n_samples = len(df_valid)
    if debug:
        print(f"[DEBUG] Filtrado: {n_samples} muestras válidas (de {len(df)})")

    # 3) Extraer bits para cada byte y concatenar
    bits_list = []
    for col in byte_cols:
        # hex → uint16
        b_int = df_valid[col].apply(lambda s: int(s, 16)).to_numpy(np.uint16)
        # máscara de byte alto → desplaza a byte bajo
        masked = ((~b_int) & 0xFF00) >> 8
        # desempacar bits little-endian → (n_samples, 8)
        bits = np.unpackbits(
            masked.astype(np.uint8)[:, None],
            axis=1, bitorder='little'
        )
        bits_list.append(bits)
    bits_array = np.hstack(bits_list).astype(bool)  # (n_samples, 8 * n_bytes)
    if debug:
        print(f"[DEBUG] Extraídos bits: matriz {bits_array.shape}")

    # 4) Métricas de falla
    # a) Instantánea por fila
    fails_inst = bits_array.sum(axis=1)
    # b) Resets tras ceros (bias correction)
    resets = (fails_inst == 0) & np.concatenate([[False], fails_inst[:-1] > 0])
    reset_indices = np.nonzero(resets)[0]
    cumsum = fails_inst.cumsum()
    bias = np.zeros_like(cumsum)
    for idx in reset_indices:
        bias[idx:] += cumsum[idx - 1]
    fails_acum = np.maximum.accumulate(cumsum + bias)
    if debug:
        print(f"[DEBUG] fails_inst y fails_acum calculados")

    # 5) Conteo de flancos y eventos periódicos
    # a) Flancos de subida
    prev = np.vstack([np.zeros(bits_array.shape[1], bool), bits_array[:-1]])
    edges = bits_array & (~prev)           # (n_samples, total_bits)
    bit_counts = edges.cumsum(axis=0)
    # b) Flancos de bajada → period events
    bits_int = bits_array.astype(np.int8)
    trans = np.diff(bits_int, axis=0,
                    prepend=np.zeros((1, bits_array.shape[1]), dtype=np.int8),
                    append=np.zeros((1, bits_array.shape[1]), dtype=np.int8))
    edges_dn = (trans == -1)[:-1]
    bit_periodic = edges_dn.cumsum(axis=0)
    if debug:
        print(f"[DEBUG] Conteo de flancos (subida y bajada) calculado")

    # 6) Asignar resultados al DataFrame
    df_valid['fails_inst'] = fails_inst
    df_valid['fails_acum'] = fails_acum
    total_bits = bits_array.shape[1]
    for i in range(total_bits):
        df_valid[f'bitn{i}'] = bit_counts[:, i]
        df_valid[f'bitnP{i}'] = bit_periodic[:, i]

    if debug:
        print(f"[DEBUG] Métricas asignadas. Pipeline completo en {time.perf_counter():.2f}s")

    # 7) Retorno idéntico en estructura
    return df_valid, (edges, resets), (edges == True, edges_dn), bit_periodic




# ---- LEGACY ----
def compute_periodic(counts: list[int], window: int = 3) -> int:
    """
    LEGACY: Count simple periodic increment patterns in a 1D count list.

    Scans through `counts` to detect occurrences of the pattern:
    [x, x+1, x+1, x], incrementing a counter for each match.

    Parameters
    ----------
    counts : list[int]
        Sequence of integer counts (e.g., per-sample failure tallies).
    window : int, default=3
        Look-back window size for pattern detection.

    Returns
    -------
    int
        Number of detected periodic patterns.

    Notes
    -----
    - The pattern logic is: counts[i] == counts[i-1] + 1,
      counts[i-1] == counts[i-2], and counts[i-2] == counts[i-3] + 1.

    Examples
    --------
    >>> compute_periodic([0,1,1,0,1,1,0], window=3)
    2
    """
    periodic = 0
    for i in range(window, len(counts)):
        if (counts[i]   == counts[i-1] + 1 and
            counts[i-1] == counts[i-2]     and
            counts[i-2] == counts[i-3] + 1 ):
            periodic += 1
    return periodic



# ---- Testing -----
if __name__ == "__main__":
    # --- testing ---

    import numpy as np
    import pandas as pd

    def legacy_mask(hex_str: str) -> int:
        """Reproduce el paso (~int(s,16) & 0xFF00) >> 8, usando 16 bits."""
        raw = int(hex_str, 16)
        comp = (~raw) & 0xFFFF               # recortar a 16 bits
        return (comp & 0xFF00) >> 8


    # 1. Preparamos datos de prueba
    sample_hex = ['0000', 'FFFF', 'A5C3', '1234', '00FF', 'FF00']
    df_test = pd.DataFrame({
        'B0': np.random.choice(sample_hex, size=1000, replace=True),
        'B1': np.random.choice(sample_hex, size=1000, replace=True),
    })

    # 2. Calculamos con legacy y con vectorizado
    legacy_b0 = df_test['B0'].apply(legacy_mask).to_numpy()
    vector_b0 = ((~(df_test['B0'].apply(lambda s: int(s,16))
                        .to_numpy(dtype=np.uint16)) & 0xFF00) >> 8)

    legacy_b1 = df_test['B1'].apply(legacy_mask).to_numpy()
    vector_b1 = ((~(df_test['B1'].apply(lambda s: int(s,16))
                        .to_numpy(dtype=np.uint16)) & 0xFF00) >> 8)
    # 3. Aserciones
    assert np.array_equal(legacy_b0, vector_b0), "Discrepancia en B0!"
    assert np.array_equal(legacy_b1, vector_b1), "Discrepancia en B1!"

    # 4. Testeo de nfails
    sample_vals = [legacy_mask(h) for h in sample_hex]
    for val in sample_vals:
        assert nfails(val) == sum((val >> i) & 1 for i in range(8)), "Error en nfails"