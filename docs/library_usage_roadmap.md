# Library Roadmap for Near-Term Probability Modeling

The latest readout in [`docs/initial_probability_models.md`](./initial_probability_models.md)
places the focus on turning the merged beam ↔ CPLD datasets into vetted Poisson
and Bayesian models.  The table below captures which `lib/` modules will be
activated over the next iteration cycle and why.

| Library | Key Helpers | Why They Matter Now | Immediate Consumers |
| --- | --- | --- | --- |
| `lib.beam` | `read_beam_data`, `beam_pipeline` | Standardise HEH monitor exports, compute beam-on flags, and prepare the dose-rate columns that feed `radbin.core.compute_scaled_time_clipped`. | `0829_bathub_corrections.ipynb`, upcoming GLM prototypes |
| `lib.cpld_io`, `lib.cpld_decode`, `lib.cpld_events` | `load_cpld_records`, `compute_counters`, `detect_bit_increments` | Transform raw CPLD dumps into timestamped bit-flip events to match the fluence bins already persisted as `results/radbin/run_3_fluence.csv`. | Failure-alignment notebooks, `radbin` QA checks |
| `lib.cpld_viz`, `lib.graphing` | `plot_bit_rate_heatmap`, `plot_bit_timeseries`, `coincidence_time` | Provide rapid feedback on synchronisation quality and bathtub structure before statistical fitting. | Presentation-ready figures, operations readouts |
| `lib.reading`, `lib.wavelet` | `import_file`, `pre_pipeline`, `cwt` | Clean and inspect verDAQ voltage/current traces so the exposure guardrails described in the Poisson bathtub doc remain defensible. | Data-quality notebooks, anomaly flagging experiments |
| `lib.detection` | `detect_latchups` | Quantify latch-up windows from DMM current streams, enabling cross-checks against CPLD/TMR failure counts. | Reliability notebooks, mitigation rulebooks |
| `lib.poisson_binning` | `build_and_summarize`, `poisson_trend_test_plus` | Thin wrapper around the `radbin` entry points already used in the bathtub study; keeps legacy notebooks running until everything is migrated. | Legacy notebooks needing compatibility |

## Upcoming Actions

1. **Re-run beam/CPLD merges** using the refreshed docstrings as inline guidance,
   producing auditable notebooks that cite the exact helpers.
2. **Instrument the Bayesian prototype** with `lib.cpld_events.detect_bit_increments`
   outputs so posterior rates are seeded from the same event counts used in the
   Poisson bathtub summary.
3. **Finalise visual readouts** with `lib.cpld_viz` and `lib.graphing` so the
   operations brief can include fluence-aligned heatmaps alongside the
   `radbin`-generated tables.
