# Mini Statistics Physics Conference: CPLD Testing Strategy

## Overview
To present the refactored CPLD analysis pipeline with statistical rigour, we
assembled a synthetic telemetry suite that can be replayed deterministically.
Each scenario recreates a physically plausible radiation upset experiment while
keeping the ground truth under our control. The resulting fixtures power the
unit tests in `tests/test_cpld_decode.py` and document the safety net protecting
the decoding logic.

## Synthetic Experimental Design
We define the experiments by enumerating which CPLD bits are asserted on each
telemetry frame. Helper utilities convert those bit schedules into the original
`B0`/`B1` hexadecimal words used by the DAQ system. The scenarios cover the
following statistical features:

| Scenario | Physical Story | Metrics Verified |
| --- | --- | --- |
| `alternating_lower_upper` | Single-shot strikes alternating between lower and upper byte latches. | `total_fails`, `total_I`, cumulative bit counts, increment events, totals summary. |
| `bias_recovery` | Bursts of simultaneous latch hits followed by recovery periods to verify bias handling. | Bias carryover in `total_I`, cumulative counters, increment events. |
| `multi_bit_reactivation` | Persistent radiation on two channels with selective reactivation. | Absence of double counts during sustained faults and accurate re-triggering. |
| `periodic_cadence` | A repetitive pinged latch that triggers the periodic cadence detector. | `bitnP*` cadence logic alongside the standard counters. |

All expected metrics are computed analytically inside the tests by replaying the
same rules as the production functions. This strategy guards against regression
creep by ensuring that any behavioural change must update both the production
code and the statistical references.

## Implementation Highlights
* **Deterministic fixtures.** Each scenario is described by a plain Python
  sequence, making it trivial to audit or extend the catalogue of experiments.
* **Closed-form expectations.** Companion helpers replicate the logic behind
  `total_I`, incremental event detection, and cadence (`bitnP*`) counters so that
  the assertions compare production results against hand-derived statistics.
* **Extensible parameterisation.** The tests rely on `pytest.mark.parametrize`
  with human-readable identifiers, enabling conference-style reports and future
  scenarios without additional boilerplate.

## Reproducing the Conference Results
Run the full statistics validation suite with:

```bash
pytest tests/test_cpld_decode.py
```

Pytest will stream each scenario name, mirroring a mini-session agenda. The
expected-vs-observed comparisons ensure that the data pipeline honours the
physics-inspired contracts encoded in the synthetic telemetry.
