# CPLD Analysis Pipeline Documentation

This document describes the pipeline used to analyze CPLD data, specifically focusing on failure analysis and "bitslip" (periodic event) calculations under continuous radiation.

## Overview

The pipeline processes raw CPLD data files, parses them into structured DataFrames, and calculates various failure metrics. The core logic is implemented in the `lib` directory, specifically `lib/cpld.py` and `lib/cpld_decode.py`.

## Key Components

### 1. Data Loading and Parsing (`lib.cpld.read_cpld_data`)

The `read_cpld_data` function reads raw data files, cleans them, and parses them into a pandas DataFrame.

-   **Input**: Path to raw data files (glob pattern).
-   **Output**:
    -   `df`: DataFrame containing valid records with columns `time`, `lfsrTMR`, `B0`, `B1`.
    -   `df_bad`: DataFrame containing timestamps of invalid records.

### 2. CPLD Pipeline (`lib.cpld.cpld_pipeline`)

The `cpld_pipeline` function is the main processing engine. It takes the parsed DataFrame and calculates:

-   **Instantaneous Failures (`fails_inst`)**: Number of failure bits set in a sample.
-   **Cumulative Failures (`fails_acum`)**: Bias-corrected cumulative failures.
-   **Bit Transitions (`bitn0`...`bitn15`)**: Cumulative rising-edge counts per bit.
-   **Periodic Events / Bitslips (`bitnP0`...`bitnP15`)**: Cumulative periodic event counts per bit.

### 3. Bitslip Calculation (Periodic Events)

The "bitslip" or "periodic event" calculation is designed to detect specific patterns in the bit counters that indicate a transient error or slip.

The logic is implemented in `lib.cpld_decode._update_periodic_counts` and `lib.cpld.compute_periodic` (legacy).

**Pattern Detection:**
The algorithm looks for a sequence of 4 samples in the cumulative bit count history: `[x, x+1, x+1, x]`.
-   `w[3] == w[2] + 1`
-   `w[2] == w[1]`
-   `w[1] == w[0] + 1`

This pattern suggests a bit flipped (count increased), stayed flipped, and then flipped back (or the counter reset in a specific way).

## Usage Example

The following example demonstrates how to use the pipeline (based on `0804_PIPE_cpld_beam.ipynb`):

```python
from lib.cpld import read_cpld_data, cpld_pipeline

# 1. Read Data
# Replace with your actual data path
cpld_path = '../0_raw/Campaign2/cpld/run/cpld_data_*.dat'
df, df_bad = read_cpld_data(cpld_path=cpld_path, debug=True)

# 2. Run Pipeline
df_valid, (edges, resets), (edges_up, edges_dn), bit_periodic = cpld_pipeline(df, debug=True)

# 3. Analyze Results
# Total periodic events (bitslips)
total_periodic_errors = bit_periodic.sum(axis=1).sum()
print(f"Total Periodic Errors: {total_periodic_errors}")

# Plot periodic events
import matplotlib.pyplot as plt
plt.plot(bit_periodic.sum(axis=1))
plt.title("Cumulative Periodic Events (Bitslips)")
plt.show()
```

## File Structure

-   `lib/cpld.py`: Main pipeline logic (`cpld_pipeline`, `read_cpld_data`).
-   `lib/cpld_decode.py`: Bit decoding and periodic event logic (`compute_counters`, `_update_periodic_counts`).
-   `lib/cpld_events.py`: Event extraction helpers.
-   `lib/cpld_viz.py`: Visualization helpers.

## Notes

-   The pipeline assumes the input data contains hex strings in columns `B0` and `B1`.
-   The "bitslip" logic is heuristic and based on observing specific counter patterns.
