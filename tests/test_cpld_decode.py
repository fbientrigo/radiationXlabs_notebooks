"""Regression tests for the CPLD decoding and event helpers."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Iterable, List, Sequence

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = REPO_ROOT / "lib"
sys.path.insert(0, str(LIB_DIR))

from cpld_decode import compute_counters, count_failed_bits, decode_word
from cpld_events import detect_bit_increments, summarise_bit_totals


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


def _expected_cumulative_counts(sequence: Sequence[Sequence[int]], n_bits: int = 16) -> List[List[int]]:
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


@pytest.mark.parametrize("mask", [0, 1, 0b11, 0b1010, 0xFF])
def test_decode_word_round_trip(mask: int) -> None:
    """``decode_word`` and ``count_failed_bits`` invert :func:`_encode_mask`."""

    word = _encode_mask(mask)
    assert decode_word(word) == mask
    assert count_failed_bits(word) == bin(mask).count("1")


def test_compute_counters_with_controlled_bit_flips() -> None:
    """Synthetic frames exercise the counter, event and summary helpers."""

    sequence = [
        [],
        [0, 8],
        [],
        [0],
        [5, 13],
        [],
    ]

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

    df = pd.DataFrame(rows)
    processed = compute_counters(df)

    expected_total_fails = [len(bits) for bits in sequence]
    assert processed["total_fails"].tolist() == expected_total_fails

    expected_total_I = [0, 2, 2, 3, 4, 4]
    assert processed["total_I"].tolist() == expected_total_I

    expected_counts = _expected_cumulative_counts(sequence)
    for bit in range(16):
        column = f"bitn{bit}"
        assert processed[column].tolist() == expected_counts[bit]

    events = detect_bit_increments(processed, time_col="time")
    expected_events = [
        (0, 1, 1),
        (8, 1, 1),
        (0, 3, 1),
        (5, 4, 1),
        (13, 4, 1),
    ]
    assert [(row.bit, row.row, row.increment) for row in events.itertuples()] == expected_events

    totals = summarise_bit_totals(processed)
    for bit in range(16):
        assert totals.loc[bit] == expected_counts[bit][-1]
