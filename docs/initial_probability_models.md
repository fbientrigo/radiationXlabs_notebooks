# Initial Probability Modeling Readout (Near-Term 2–4 Weeks)

## Context
We are now operating in the near-term execution window, where the priority is to turn the
Poisson bathtub exploration into reproducible probability models that connect beam flux,
CPLD/TMR failures, and area-normalized cross sections. The latest analysis notebook
[`0829_bathub_corrections.ipynb`](../0829_bathub_corrections.ipynb) consolidates the
merged beam ↔ CPLD datasets and exercises the `radbin` toolkit to prototype those models.
This document distills the notebook flow and clarifies how the reusable libraries support the
next wave of model development.

## Data & Libraries in Play
- **Beam & failure streams**: `1_data/beam3.csv` (HEH monitor with dose rate, on/off state)
  and the validated failure log used to generate `results/radbin/run_3_fluence.csv`.
- **RadBIN core** (`radbin/core.py`):
  - `to_datetime_smart` harmonizes the multiple timestamp encodings coming from the data
    loggers.
  - `compute_scaled_time_clipped` builds the equivalent-time track either in reference-time
    or fluence mode, including adaptive floors and beam-off freezing.
  - `build_and_summarize` orchestrates bin construction (fluence, reset-locked, equal-count)
    and returns Garwood interval summaries plus gap statistics for inter-failure fluence.
- **RadBIN visualization utilities** (`radbin/plots.py`): `bar_rates`, `plot_cumulative_fails`,
  `plot_scaling_ratio` render cross-section trends, cumulative counts, and scaling quality
  checks for reporting.
- **RadBIN GLM helpers** (`radbin/glm.py`): `poisson_trend_test` and
  `poisson_trend_test_plus` remain available for trend diagnostics once bin outputs are
  finalized; the notebook keeps the hooks commented until the fluence bins are fully vetted.

## Notebook Flow (0829 Bathub Corrections)
1. **Imports & configuration** – pulls the RadBIN core/plot/GLM helpers and configures the
   run context (`run_id=3`, bin counts, Garwood tail probability, and area normalization to a
   single subsystem).
2. **Data loading & normalization** – loads the beam/failure CSVs, converts timestamps with
   `to_datetime_smart`, and materializes fluence-scaled time via
   `compute_scaled_time_clipped(mode="fluence")` for inspection (`inspect_scaled_time`).
3. **Beam-on gating** – aligns failure events with the beam step function through
   `merge_asof`, preserving only failures that occur under active beam exposure.
4. **Exposure guardrails** – computes the total fluence-equivalent time and derives a
   minimum exposure (`T_min`) set to 20 % of the ideal bin allocation to keep bins from being
   dominated by very low-fluence segments.
5. **Fluence binning** – calls `build_and_summarize` with `bin_mode="fluence"`, the
   area-normalization pair `(area_run=32, area_ref=1)`, the beam-on filtered failures, the
   exposure floor (`min_exposure_per_bin=T_min`), and `min_events_per_bin=5`. The output is a
   21-bin table persisted to `results/radbin/run_3_fluence.csv` and visualized via
   `bar_rates`.
6. **Cross-section construction** – derives the single-event cross section per bin as
   `sigma_SEE = N / T`, matching the physics framing from Melanie Berg. This is the quantity
   plotted on a log scale and used downstream to characterize bathtub dynamics.
7. **Quality plots** – produces cumulative-failure and scaling-ratio diagnostics to verify
   counting consistency and the behaviour of the fluence scaling.

## Current Quantitative Readout
The fluence-binned summary for Run 3 already lives in
`results/radbin/run_3_fluence.csv`. Descriptive statistics of the per-bin counts, exposures,
and cross sections are:

| Metric | N (events) | T (fluence-equivalent time) | σ<sub>SEE</sub> (events / T) |
| --- | ---: | ---: | ---: |
| count | 21 | 21 | 21 |
| mean | 5.22 × 10³ | 1.58 × 10¹⁰ | 7.61 × 10⁻⁶ |
| median | 4.39 × 10³ | 1.66 × 10¹⁰ | 2.87 × 10⁻⁷ |
| min | 8.70 × 10² | 5.68 × 10⁶ | 6.58 × 10⁻⁸ |
| max | 1.95 × 10⁴ | 1.67 × 10¹⁰ | 1.53 × 10⁻⁴ |

Additional checkpoints already computed in the notebook artifacts:
- **Median rate (Garwood)** ≈ 9.0 × 10⁻⁹ events / fluence-unit after area normalization.
- **Gap statistics** (`gap_mean`, `gap_p10`, `gap_p99`, …) reveal how inter-failure fluence
  evolves across the beam campaign and give us early signals of bathtub regions.

## Implications for Initial Probability Models
- The **beam-on filtered bins** plus `sigma_SEE` provide directly interpretable targets for
  both Poisson GLMs and Bayesian hazard models—each bin behaves like a Poisson exposure
  experiment with known T.
- **Area normalization** is already wired, so model outputs can be reported per-subsystem or
  scaled back to full-system exposures by adjusting `(area_run, area_ref)`.
- The **exposure floor** and **minimum events per bin** guard against over-dispersion caused by
  sparse intervals, giving stable variance for trend tests (`poisson_trend_test`) and for the
  forthcoming Bayesian change-point analyses.

## Next Modeling Actions (2–4 Week Horizon)
1. **Trend Diagnostics** – run `poisson_trend_test_plus` on `results/radbin/run_3_fluence.csv`
   (and the analogous outputs for other runs) to quantify any monotonic drift in
   σ<sub>SEE</sub> across the campaign, toggling `se_method="robust"` to absorb moderate
   over-dispersion.
2. **Posterior Prototyping** – wire the fluence bins into the Bayesian bathtub notebook,
   seeding a piecewise-constant hazard model where each bin’s `(N, T)` pair informs the rate
   priors. Use the gap summaries as hyper-prior hints for failure spacing.
3. **Operational Packaging** – finalize plots (`bar_rates`, cumulative, scaling ratio) with
   consistent labeling so they can be lifted directly into stakeholder briefings while the
   probabilistic back-ends are still being tuned.

With these steps, the team can iterate quickly on Poisson-based initial models while keeping
physics interpretable outputs (σ<sub>SEE</sub>, fluence gaps) at the forefront for the 2–4 week
milestones.
