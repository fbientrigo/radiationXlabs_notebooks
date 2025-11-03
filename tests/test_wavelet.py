import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

import sys
from pathlib import Path
import importlib.util

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

spec = importlib.util.spec_from_file_location("lib.wavelet", root / "lib" / "wavelet.py")
wavelet = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(wavelet)


def test_cwt_accepts_explicit_sampling_period(monkeypatch):
    timestamps = pd.date_range("2022-01-01", periods=64, freq="1ms")
    df = pd.DataFrame({
        "timestamp": timestamps,
        "ch0": np.sin(np.linspace(0, 4 * np.pi, len(timestamps)))
    })

    monkeypatch.setattr(wavelet.plt, "show", lambda *args, **kwargs: None)

    wavelet.cwt(df, sampling_period=1e-3)


@pytest.fixture
def hex_dataframe():
    n = 128
    timestamps = pd.date_range("2022-01-01", periods=n, freq="1ms")
    base = np.arange(n) % 256
    data = {f"ch{i}": [f"{val:02X}" for val in base] for i in range(8)}
    data["timestamp"] = timestamps
    return pd.DataFrame(data)


def test_analyze_frequencies_runs_with_sampling_period(monkeypatch, hex_dataframe):
    monkeypatch.setattr(wavelet.plt, "show", lambda *args, **kwargs: None)

    wavelet.analyze_frequencies(hex_dataframe, channel="ch0", sampling_period=1e-3)
