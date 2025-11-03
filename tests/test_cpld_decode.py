"""Regression tests for the CPLD decoding and event helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Sequence

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = REPO_ROOT / "lib"
sys.path.insert(0, str(LIB_DIR))

from cpld_decode import compute_counters, count_failed_bits, decode_word
from cpld_events import detect_bit_increments, summarise_bit_totals


@dataclass(frozen=True)
class Scenario:
    """Container for a synthetic CPLD experiment.

    Parameters
    ----------
    name:
        Human readable identifier used by :mod:`pytest` when parameterising the
        regression suite.
    sequence:
        Collection of rows where each item lists the bits that are set to ``1``
        in that sample.  The helper utilities convert it into the ``B0``/``B1``
        register representation.
    expected_total_I:
        Optional sequence with the expected values for the ``total_I`` column.
        When omitted the tests derive it from :attr:`sequence` using the
        notebook heuristics.
    expected_periodic:
        Optional mapping from bit index to the full time-series of periodic
        counters.  This provides a clear contract for the cadence detection
        logic implemented in :func:`compute_counters`.
    """

    name: str
    sequence: Sequence[Sequence[int]]
    expected_total_I: Sequence[int] | None = None
    expected_periodic: Dict[int, Sequence[int]] | None = None


def _encode_mask(mask: int) -> str:
    """Return the hexadecimal representation that decodes back to ``mask``."""

    return f"{(~(mask << 8)) & 0xFFFF:04X}"


def _build_words(active_bits: Iterable[int]) -> tuple[str, str]:
    """Convert a collection of bit indices into the corresponding words."""

    lower_mask = 0
    upper_mask = 0
    for bit in active_bits:
        if bit < 8:
            lower_mask |= 1 << bit
        else:
            upper_mask |= 1 << (bit - 8)
    return _encode_mask(lower_mask), _encode_mask(upper_mask)


def _expected_cumulative_counts(
    sequence: Sequence[Sequence[int]], n_bits: int = 16
) -> List[List[int]]:
    """Return per-row cumulative counts for each bit in ``sequence``."""

    history = [[0] * len(sequence) for _ in range(n_bits)]
    prev_state = [0] * n_bits
    totals = [0] * n_bits

    for row_index, active_bits in enumerate(sequence):
        current_state = [0] * n_bits
        for bit in active_bits:
            current_state[bit] = 1
        for bit in range(n_bits):
            if prev_state[bit] == 0 and current_state[bit] == 1:
                totals[bit] += 1
            history[bit][row_index] = totals[bit]
            prev_state[bit] = current_state[bit]
    return history


def _expected_total_I(sequence: Sequence[Sequence[int]]) -> List[int]:
    """Replicate the ``total_I`` accumulation from ``compute_counters``."""

    bias = 0
    prev_total = 0
    prev_fails = 0
    totals: List[int] = []
    for bits in sequence:
        fails = len(bits)
        if fails == 0 and prev_fails != 0:
            bias = prev_total
        total = fails + bias
        if totals and total < prev_total:
            total = prev_total
        totals.append(total)
        prev_total = total
        prev_fails = fails
    return totals


def _expected_events(
    sequence: Sequence[Sequence[int]], n_bits: int = 16
) -> List[tuple[int, int, int]]:
    """Return the row index and increment for each detected bit transition."""

    counts = _expected_cumulative_counts(sequence, n_bits)
    events: List[tuple[int, int, int]] = []

    for bit in range(n_bits):
        prev = 0
        for row_index, value in enumerate(counts[bit]):
            diff = value - prev
            if diff > 0:
                events.append((bit, row_index, diff))
            prev = value

    events.sort(key=lambda entry: (entry[1], entry[0]))
    return events


def _expected_periodic_counts(
    sequence: Sequence[Sequence[int]], n_bits: int = 16
) -> List[List[int]]:
    """Mirror the cadence detector used for the ``bitnP*`` columns."""

    history = {bit: [] for bit in range(n_bits)}
    periodic_totals = [0] * n_bits
    traces = [[0] * len(sequence) for _ in range(n_bits)]
    cumulative = [0] * n_bits
    prev_state = [0] * n_bits

    for row_index, active_bits in enumerate(sequence):
        current_state = [0] * n_bits
        for bit in active_bits:
            current_state[bit] = 1

        for bit in range(n_bits):
            if prev_state[bit] == 0 and current_state[bit] == 1:
                cumulative[bit] += 1

            history[bit].append(cumulative[bit])
            if len(history[bit]) >= 4:
                w = history[bit][-4:]
                if w[3] == w[2] + 1 and w[2] == w[1] and w[1] == w[0] + 1:
                    periodic_totals[bit] += 1
            history[bit] = history[bit][-4:]
            traces[bit][row_index] = periodic_totals[bit]
            prev_state[bit] = current_state[bit]

    return traces


def _frame_from_sequence(sequence: Sequence[Sequence[int]]) -> pd.DataFrame:
    """Construct a DataFrame mimicking CPLD telemetry for ``sequence``."""

    rows = []
    for idx, bits in enumerate(sequence):
        b0_word, b1_word = _build_words(bits)
        rows.append(
            {
                "time": pd.to_datetime(idx, unit="s"),
                "B0": b0_word,
                "B1": b1_word,
            }
        )
    return pd.DataFrame(rows)


@pytest.mark.parametrize("mask", [0, 1, 0b11, 0b1010, 0xFF])
def test_decode_word_round_trip(mask: int) -> None:
    """``decode_word`` and ``count_failed_bits`` invert :func:`_encode_mask`."""

    word = _encode_mask(mask)
    assert decode_word(word) == mask
    assert count_failed_bits(word) == bin(mask).count("1")


def _pulse_train(bit: int, pulses: int) -> List[List[int]]:
    """Return an alternating on/off sequence for ``bit`` using ``pulses`` cycles."""

    sequence: List[List[int]] = [[]]
    for _ in range(pulses):
        sequence.append([bit])
        sequence.append([])
    return sequence


SCENARIOS: List[Scenario] = [
    Scenario(
        name="alternating_lower_upper",
        sequence=[
            [],
            [0, 8],
            [],
            [0],
            [5, 13],
            [],
        ],
    ),
    Scenario(
        name="bias_recovery",
        sequence=[
            [0, 8],
            [0, 8],
            [],
            [0],
            [],
            [8],
            [],
        ],
    ),
    Scenario(
        name="multi_bit_reactivation",
        sequence=[
            [1, 9],
            [1, 9],
            [],
            [9],
            [],
            [1, 9],
        ],
    ),
    Scenario(
        name="periodic_cadence",
        sequence=_pulse_train(bit=0, pulses=4),
        expected_periodic={
            0: [0, 0, 0, 1, 1, 2, 2, 3, 3],
        },
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.name)
def test_compute_counters_with_synthetic_scenarios(scenario: Scenario) -> None:
    """Exercise the counter, event and summary helpers with synthetic data."""

    df = _frame_from_sequence(scenario.sequence)
    processed = compute_counters(df)

    expected_total_fails = [len(bits) for bits in scenario.sequence]
    assert processed["total_fails"].tolist() == expected_total_fails

    expected_total_I = (
        list(scenario.expected_total_I)
        if scenario.expected_total_I is not None
        else _expected_total_I(scenario.sequence)
    )
    assert processed["total_I"].tolist() == expected_total_I

    expected_counts = _expected_cumulative_counts(scenario.sequence)
    for bit in range(16):
        column = f"bitn{bit}"
        assert processed[column].tolist() == expected_counts[bit]

    events = detect_bit_increments(processed, time_col="time")
    expected_events = _expected_events(scenario.sequence)
    assert [(row.bit, row.row, row.increment) for row in events.itertuples()] == expected_events

    totals = summarise_bit_totals(processed)
    for bit in range(16):
        assert totals.loc[bit] == expected_counts[bit][-1]

    periodic_expectations = scenario.expected_periodic or {}
    if periodic_expectations:
        periodic_counts = _expected_periodic_counts(scenario.sequence)
        for bit, expected_series in periodic_expectations.items():
            column = f"bitnP{bit}"
            assert processed[column].tolist() == list(expected_series)
            assert periodic_counts[bit] == list(expected_series)
