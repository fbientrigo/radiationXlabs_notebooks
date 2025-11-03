"""Utilities for loading raw CPLD telemetry dumps.

The helpers bridge raw dumps and the modeling notebooks described in
``docs/initial_probability_models.md`` by providing clean timestamped tables.
"""

This module concentrates the notebook logic used to locate and parse the
``cpld_data_*.dat`` files generated during irradiation runs.  The functions are
lightweight wrappers around :mod:`pandas` that:

* normalise the ASCII dumps (removing helper characters such as ``*``),
* convert the timestamp column into timezone aware :class:`datetime`
  information,
* and concatenate multiple files into a single :class:`~pandas.DataFrame`.

Examples
--------
>>> from pathlib import Path
>>> from lib.cpld_io import load_cpld_records
>>> folder = Path('ThirdRunAna/Rad_CPLD_november/data_run')
>>> df = load_cpld_records(folder.glob('cpld_data_*.dat'))
>>> df.columns[:4].tolist()
['time', 'lfsrTMR', 'B0', 'B1']
"""
from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Iterable, Iterator, Sequence, Union

import pandas as pd

__all__ = [
    "CPLDRecord",
    "clean_ascii_dump",
    "load_cpld_file",
    "load_cpld_records",
]


@dataclass
class CPLDRecord:
    """Simple container describing a CPLD telemetry file.

    Parameters
    ----------
    path:
        Path to the raw ``.dat`` file on disk.
    rows:
        Number of payload rows discovered in the file (after removing comment
        lines).  This is computed lazily while reading the file contents.
    """

    path: Path
    rows: int


DEFAULT_NAMES: Sequence[str] = ("time", "lfsrTMR", "B0", "B1")


def clean_ascii_dump(text: str) -> str:
    """Normalise the content of a CPLD dump file.

    The archived notebooks store the data as ASCII text where comment markers
    (``*``) and the pattern ``" #"`` need to be removed before parsing.  This
    helper mirrors the transformations implemented in
    ``archive/CPLD_data_ana_Run3.ipynb``.

    Parameters
    ----------
    text:
        Raw content as read from disk.

    Returns
    -------
    str
        The cleaned CSV-like string ready to be consumed by
        :func:`pandas.read_csv`.

    Examples
    --------
    >>> clean_ascii_dump('2022,*\n #comment')
    '2022,\n,comment'
    """

    return text.replace("*", "").replace(" #", ",")


def _to_datetime(series: pd.Series, tz_offset_hours: float = 0.0) -> pd.Series:
    """Convert a numeric timestamp series into datetime values.

    The raw files store the timestamp as seconds since epoch.  We first coerce
    the column to numeric and then let :func:`pandas.to_datetime` perform the
    conversion.  A constant offset (in hours) can be added to account for local
    time representations used during the run.
    """

    seconds = pd.to_numeric(series, errors="coerce")
    dt = pd.to_datetime(seconds, unit="s", origin="unix", errors="coerce")
    if tz_offset_hours:
        dt = dt + pd.to_timedelta(tz_offset_hours, unit="h")
    return dt


def load_cpld_file(
    path: Union[str, Path],
    names: Sequence[str] = DEFAULT_NAMES,
    tz_offset_hours: float = 0.0,
) -> pd.DataFrame:
    """Load a single CPLD ``.dat`` file into a DataFrame.

    Parameters
    ----------
    path:
        Location of the file on disk.
    names:
        Column names to assign when reading the CSV data.  The default
        reproduces the structure seen in the notebooks (``time``, ``lfsrTMR``,
        ``B0`` and ``B1``).
    tz_offset_hours:
        Optional offset (in hours) applied to the timestamp column.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the parsed data sorted by timestamp and without
        rows where ``B0`` or ``B1`` could not be decoded.

    Examples
    --------
    >>> from pathlib import Path
    >>> sample = Path('tests/data/cpld_sample.dat')
    >>> df = load_cpld_file(sample)
    >>> df.head(1)[['B0', 'B1']].iloc[0].tolist()
    ['FF00', 'FF00']
    """

    path = Path(path)
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    cleaned = clean_ascii_dump(raw_text)
    buffer = StringIO(cleaned)
    df = pd.read_csv(
        buffer,
        sep=",",
        header=None,
        names=names,
        engine="python",
        parse_dates=False,
        on_bad_lines="skip",
    )

    if "time" in df.columns:
        df["time"] = _to_datetime(df["time"], tz_offset_hours=tz_offset_hours)

    df = df.dropna(subset=["B0", "B1"]).sort_values("time").reset_index(drop=True)
    return df


def load_cpld_records(
    paths: Iterable[Union[str, Path]],
    names: Sequence[str] = DEFAULT_NAMES,
    tz_offset_hours: float = 0.0,
) -> pd.DataFrame:
    """Load several CPLD files and concatenate them into a single DataFrame.

    Parameters
    ----------
    paths:
        Iterable with the files to read.  ``pathlib.Path.glob`` is a convenient
        generator for this argument.
    names:
        Column names to assign to the parsed CSV data.
    tz_offset_hours:
        Optional timezone offset applied to the timestamp column of every
        individual file.

    Returns
    -------
    pandas.DataFrame
        Concatenated data sorted by timestamp.

    Examples
    --------
    >>> from pathlib import Path
    >>> folder = Path('ThirdRunAna/Rad_CPLD_november/data_run')
    >>> df = load_cpld_records(folder.glob('cpld_data_*.dat'))
    >>> len(df.columns)
    4
    """

    data_frames = [
        load_cpld_file(path, names=names, tz_offset_hours=tz_offset_hours)
        for path in paths
    ]
    if not data_frames:
        return pd.DataFrame(columns=names)

    combined = pd.concat(data_frames, ignore_index=True)
    if "time" in combined.columns:
        combined = combined.sort_values("time").reset_index(drop=True)
    return combined


def iter_cpld_records(
    root: Union[str, Path],
    pattern: str = "cpld_data_*.dat",
) -> Iterator[CPLDRecord]:
    """Iterate over CPLD files located under ``root``.

    This generator yields :class:`CPLDRecord` instances describing each file
    discovered.  It is particularly useful when analysing large runs because it
    lets the caller lazily decide whether to load the heavy payload.

    Examples
    --------
    >>> from lib.cpld_io import iter_cpld_records
    >>> for record in iter_cpld_records('ThirdRunAna', 'cpld_data_*.dat'):
    ...     print(record.path.name)
    ...     break
    cpld_data_2022_09_15_135543_00006.dat
    """

    root = Path(root)
    for path in sorted(root.glob(pattern)):
        text = path.read_text(encoding="utf-8", errors="ignore")
        cleaned = clean_ascii_dump(text)
        rows = sum(1 for line in cleaned.splitlines() if line.strip())
        yield CPLDRecord(path=path, rows=rows)
