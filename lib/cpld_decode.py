"""Bit decoding utilities for CPLD telemetry frames.

The helpers produce bit-flip timelines used by the Poisson bathtub notebooks
and the roadmap in ``docs/initial_probability_models.md``.
"""

The original ``archive/CPLD_data_ana_Run3.ipynb`` notebook performed the
conversion of the hexadecimal ``B0``/``B1`` columns into per-bit counters.  This
module provides a tested, well documented Python API that mirrors that logic.

from __future__ import annotations

from typing import List, MutableMapping

import numpy as np
import pandas as pd

__all__ = [
    "decode_word",
    "count_failed_bits",
    "compute_counters",
]

_MASK = 0xFF00
_SHIFT = 8


def decode_word(word: str) -> int:
    """Convert a hexadecimal CPLD register into an integer mask.

    Parameters
    ----------
    word:
        Hexadecimal representation of the register.  The function accepts both
        uppercase and lowercase characters.

    Returns
    -------
    int
        Integer mask with the eight least significant bits representing the
        status of each failure flag.  ``1`` indicates a bit flip.

    Examples
    --------
    >>> decode_word('FF00')
    0
    >>> bin(decode_word('FE00'))
    '0b1'
    """

    if not isinstance(word, str):
        raise TypeError("The CPLD word must be provided as a hexadecimal string.")

    try:
        raw = int(word, 16)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Cannot decode CPLD word '{word}'.") from exc

    return ((~raw) & _MASK) >> _SHIFT


def count_failed_bits(word: str) -> int:
    """Return how many individual bits are flagged as failing for ``word``.

    The CPLD exposes the failure latches as cleared bits in the hexadecimal
    register value (``0`` means the bit tripped).  The archived notebook
    inverted the word, masked the upper byte and counted how many flags were
    active.  This helper performs the exact same sequence so that both the
    refactored code base and the historical analysis agree on the semantics of
    a "failed" bit.

    Examples
    --------
    >>> count_failed_bits('FE00')
    1
    >>> count_failed_bits('FC00')
    2
    """

    mask = decode_word(word)
    return int(bin(mask).count("1"))


def _update_periodic_counts(
    history: MutableMapping[int, List[int]],
    current_counts: np.ndarray,
    periodic_counts: np.ndarray,
) -> None:
    """Update the periodic counters following the notebook heuristics."""

    for bit, value in enumerate(current_counts):
        bit_history = history.setdefault(bit, [])
        bit_history.append(int(value))
        if len(bit_history) >= 4:
            w = bit_history[-4:]
            if w[3] == w[2] + 1 and w[2] == w[1] and w[1] == w[0] + 1:
                periodic_counts[bit] += 1
        history[bit] = bit_history[-4:]


def compute_counters(
    df: pd.DataFrame,
    b0_col: str = "B0",
    b1_col: str = "B1",
    time_col: str = "time",
    n_bits: int = 16,
) -> pd.DataFrame:
    """Augment ``df`` with the CPLD counters extracted from ``B0`` and ``B1``.

    The implementation follows closely the imperative code that lived inside the
    notebook.  Internally the function decodes the hexadecimal words, tracks
    edge transitions (0→1) for each bit and computes auxiliary counters used for
    visualisations.

    Parameters
    ----------
    df:
        Input DataFrame containing the raw telemetry columns.
    b0_col, b1_col:
        Names of the columns holding the hexadecimal strings.
    time_col:
        Name of the timestamp column.  It is used exclusively for sorting.
    n_bits:
        Total number of bits to track.  The default (16) matches the CPLD
        register layout.

    Returns
    -------
    pandas.DataFrame
        Copy of the input data with additional columns: ``B0_nfails``,
        ``B1_nfails``, ``total_fails``, ``total_I``, ``bitn*`` and ``bitnP*``.

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({
    ...     'time': pd.to_datetime([0, 1, 2], unit='s'),
    ...     'B0': ['FF00', 'FE00', 'FF00'],
    ...     'B1': ['FF00', 'FF00', 'FF00'],
    ... })
    >>> processed = compute_counters(data)
    >>> processed.loc[:, ['total_fails', 'total_I', 'bitn0']].values.tolist()
    [[0, 0, 0], [1, 1, 1], [0, 1, 1]]
    """

    if df.empty:
        return df.copy()

    if n_bits % 2:
        raise ValueError("`n_bits` must be an even number (two bytes of data).")

    data = df.sort_values(time_col).reset_index(drop=True).copy()
    bit_columns = [f"bitn{i}" for i in range(n_bits)]
    periodic_columns = [f"bitnP{i}" for i in range(n_bits)]

    for column in (b0_col, b1_col):
        if column not in data.columns:
            raise KeyError(f"Column '{column}' is required to compute CPLD counters.")

    total_rows = len(data)
    bit_counts_matrix = np.zeros((total_rows, n_bits), dtype=int)
    periodic_matrix = np.zeros((total_rows, n_bits), dtype=int)

    cumulative_bit_counts = np.zeros(n_bits, dtype=int)
    periodic_counts = np.zeros(n_bits, dtype=int)
    periodic_history: MutableMapping[int, List[int]] = {}

    prev_bits = np.zeros(n_bits, dtype=int)
    total_integrated = np.zeros(total_rows, dtype=int)
    total_fails = np.zeros(total_rows, dtype=int)
    b0_fails = np.zeros(total_rows, dtype=int)
    b1_fails = np.zeros(total_rows, dtype=int)
    bias = 0

    for idx, (word0, word1) in enumerate(zip(data[b0_col], data[b1_col])):
        try:
            mask0 = decode_word(str(word0))
            mask1 = decode_word(str(word1))
        except (TypeError, ValueError):
            if idx > 0:
                bit_counts_matrix[idx] = bit_counts_matrix[idx - 1]
                periodic_matrix[idx] = periodic_matrix[idx - 1]
                total_integrated[idx] = total_integrated[idx - 1]
                total_fails[idx] = total_fails[idx - 1]
                b0_fails[idx] = b0_fails[idx - 1]
                b1_fails[idx] = b1_fails[idx - 1]
            continue

        lower_bits = np.array([(mask0 >> bit) & 1 for bit in range(n_bits // 2)], dtype=int)
        upper_bits = np.array([(mask1 >> bit) & 1 for bit in range(n_bits // 2)], dtype=int)
        bits = np.concatenate([lower_bits, upper_bits])

        b0_fails[idx] = count_failed_bits(str(word0))
        b1_fails[idx] = count_failed_bits(str(word1))
        total_fails[idx] = int(b0_fails[idx] + b1_fails[idx])

        if idx > 0 and total_fails[idx] == 0 and total_fails[idx - 1] != 0:
            bias = total_integrated[idx - 1]

        total_integrated[idx] = total_fails[idx] + bias
        if idx > 0 and total_integrated[idx] < total_integrated[idx - 1]:
            total_integrated[idx] = total_integrated[idx - 1]

        transitions = (prev_bits == 0) & (bits == 1)
        cumulative_bit_counts += transitions.astype(int)
        bit_counts_matrix[idx] = cumulative_bit_counts

        _update_periodic_counts(periodic_history, cumulative_bit_counts, periodic_counts)
        periodic_matrix[idx] = periodic_counts

        prev_bits = bits

    for col, values in zip(bit_columns, bit_counts_matrix.T):
        data[col] = values
    for col, values in zip(periodic_columns, periodic_matrix.T):
        data[col] = values

    data["B0_nfails"] = b0_fails
    data["B1_nfails"] = b1_fails
    data["total_fails"] = total_fails
    data["total_I"] = total_integrated
    data["count"] = np.arange(total_rows, dtype=int)

    return data
