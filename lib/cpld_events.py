from __future__ import annotations
"""Event extraction helpers for CPLD bit-flip counters."""

"""Event extraction utilities for CPLD bit-flip counters.

The resulting tables feed the fluence-aligned failure analysis captured in
``docs/initial_probability_models.md`` and the associated Poisson bathtub
notebooks.
"""


from typing import List

import pandas as pd

__all__ = ["detect_bit_increments", "summarise_bit_totals"]


def _bit_columns(df: pd.DataFrame, prefix: str) -> List[str]:
    columns = [col for col in df.columns if col.startswith(prefix) and col[len(prefix) :].isdigit()]
    return sorted(columns, key=lambda name: int(name[len(prefix) :]))


def detect_bit_increments(
    df: pd.DataFrame,
    bit_prefix: str = "bitn",
    time_col: str = "time",
    minimum_increment: int = 1,
) -> pd.DataFrame:
    """Identify the rows where a bit counter increased.

    Parameters
    ----------
    df:
        DataFrame produced by :func:`lib.cpld_decode.compute_counters`.
    bit_prefix:
        Prefix that identifies the per-bit counter columns.
    time_col:
        Name of the timestamp column.  If present, it is copied to the output
        and used for sorting.
    minimum_increment:
        Minimum difference required to register an event.  The default ``1``
        matches the behaviour from the original notebook.

    Returns
    -------
    pandas.DataFrame
        Event table with the following columns: ``bit`` (integer index of the
        bit), ``row`` (row location within ``df``), ``increment`` (difference
        observed) and ``count`` (new cumulative value).  When ``time_col`` exists
        in ``df`` it is included in the output as well.

    Examples
    --------
    >>> import pandas as pd
    >>> from lib.cpld_events import detect_bit_increments
    >>> df = pd.DataFrame({
    ...     'time': pd.to_datetime([0, 1, 2], unit='s'),
    ...     'bitn0': [0, 1, 1],
    ...     'bitn1': [0, 0, 1],
    ... })
    >>> events = detect_bit_increments(df)
    >>> events[['bit', 'row', 'increment']].values.tolist()
    [[0, 1, 1], [1, 2, 1]]
    """

    columns = _bit_columns(df, bit_prefix)
    if not columns:
        raise ValueError(f"No columns starting with '{bit_prefix}' were found.")

    records: List[dict] = []
    for col in columns:
        bit_index = int(col[len(bit_prefix) :])
        counts = pd.to_numeric(df[col], errors="coerce").ffill().fillna(0)
        increments = counts.diff().fillna(counts)
        mask = increments >= minimum_increment
        if not mask.any():
            continue

        for row_idx in df.index[mask]:
            record = {
                "bit": bit_index,
                "row": int(row_idx),
                "increment": int(increments.loc[row_idx]),
                "count": int(counts.loc[row_idx]),
            }
            if time_col in df.columns:
                record[time_col] = df.loc[row_idx, time_col]
            records.append(record)

    events_df = pd.DataFrame.from_records(records)
    if events_df.empty:
        return events_df

    if time_col in events_df.columns:
        events_df = events_df.sort_values(by=[time_col, "bit", "row"]).reset_index(drop=True)
    else:
        events_df = events_df.sort_values(by=["row", "bit"]).reset_index(drop=True)
    return events_df


def summarise_bit_totals(
    df: pd.DataFrame,
    bit_prefix: str = "bitn",
) -> pd.Series:
    """Return the final count per bit.

    The series is indexed by the bit number and contains the maximum value
    observed for each counter.

    Examples
    --------
    >>> import pandas as pd
    >>> from lib.cpld_events import summarise_bit_totals
    >>> df = pd.DataFrame({'bitn0': [0, 1], 'bitn1': [0, 2]})
    >>> summarise_bit_totals(df).to_dict()
    {0: 1, 1: 2}
    """

    columns = _bit_columns(df, bit_prefix)
    if not columns:
        raise ValueError(f"No columns starting with '{bit_prefix}' were found.")

    totals = {}
    for col in columns:
        values = pd.to_numeric(df[col], errors="coerce").ffill().fillna(0)
        totals[int(col[len(bit_prefix) :])] = int(values.max())
    series = pd.Series(totals, name="total_events").sort_index()
    return series
