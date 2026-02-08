# RadAnalysis: Stochastic Simulation of TMR Architectures
> **Framework for Soft Error Rate Estimation under Mixed-Field Radiation**

## 1. Overview
**RadAnalysis** is a computational framework designed to simulate the stochastic behavior of Triple Modular Redundancy (TMR) digital systems exposed to ionizing radiation. The system models the competition between Single Event Upsets (SEUs) driven by particle flux and the corrective "Scrubbing" mechanism, enabling the verification of reliability models and the visualization of failure modes.

## 2. Theoretical Model

### 2.1 Radiation Interaction (Poisson Process)
The probability of a single bit upset (SEU) occurring in a time interval $\Delta t$ is modeled as a Poisson process, derived from the particle fluence:

$$ P_{flip} = 1 - e^{-\sigma \cdot \Phi \cdot \Delta t} $$

Where:
*   $\Phi$: Particle Flux ($particles/cm^2/s$).
*   $\sigma$: Cross Section ($cm^2/device$).
*   $\Delta t$: Simulation time step ($s$).

This model assumes that events are independent and identically distributed (i.i.d.) in time, valid for constant or slowly varying beams.

### 2.2 TMR Logic State Machine
Each logical unit (Triad) controls 3 physical bits. The state of the $i$-th triad at time $t$ is determined by the Hamming distance of its bits relative to the "Correct" state (000):

1.  **Nominal (State 0)**: 0 upsets. System fully functional.
2.  **Masked Error (State 1)**: 1 upset (e.g., 001). The TMR voter masks the error; the output remains correct.
3.  **System Failure (State 2)**: $\ge 2$ upsets (e.g., 011). The voter is defeated; output is corrupted.

The simulation vectorizes this state evaluation over $N$ triads (typically $N=10^4$) using NumPy for high-throughput Monte Carlo estimation.

### 2.3 Corrective Mechanism (Scrubbing)
Regular "Scrubbing" resets all bits to the Nominal state. The interval between scrubs $T_{scrub}$ is modeled as a Gaussian random variable to account for clock jitter or system latency:

$$ T_{scrub} \sim \mathcal{N}(\mu_{scrub}, \sigma_{scrub}^2) $$

## 3. Statistical Methodology

### 3.1 Observed Failure Rate ($\lambda_{obs}$)
We estimate the failure rate (Cross Section equivalent) by counting the number of discrete SEU events $k$ over a window $T$:

$$ \lambda_{obs} = \frac{k}{T \cdot N_{devices}} $$

The system tracks two variants:
*   **Windowed $\lambda$**: Local estimate over the last $W$ seconds (e.g., 2s). Captures instantaneous beam structure.
*   **Cumulative $\lambda_{avg}$**: Integrated estimate from $t=0$. Converges to the true mean.

### 3.2 Theoretical Reference
The theoretical upset rate per device is strictly:
$$ \lambda_{theory} = \Phi \times \sigma $$
*Note: This refers to the bit upset rate, not the TMR system failure rate.*

### 3.3 Convergence & Confidence
Assuming SEUs follow a Poisson distribution, the standard error of the rate estimate scales as:
$$ \text{Convergence} \propto \frac{1}{\sqrt{k}} $$
We calculate 95% Confidence Intervals (CI) for the observed rate:
$$ CI_{95\%} = \lambda_{obs} \pm 1.96 \sqrt{\frac{\lambda_{obs}}{T}} $$

## 4. Usage Guide

The simulation environment requires the `rad-env` conda environment.

### 4.1 Numerical Monitor (Terminal)
Use this for long-running statistical validation without GUI overhead.

```bash
python run_simulation.py --flux 5e7 --triads 10000 --dt 0.01
```

**Key Metrics displayed:**
- **System Failures**: Count of triads currently in State 2 (Defeated).
- **Masked Errors**: Count of triads in State 1 (Saved by TMR).
- **Lambda Avg**: Should converge to Flux $\times$ Sigma.

### 4.2 Visualization (GUI)
Use this to analyze the temporal dynamics of errors and the efficacy of scrubbing.

```bash
# Standard view
python visualize.py --flux 2e7 --triads 2500

# High-Dynamic Range (Logarithmic)
python visualize.py --flux 1e8 --log

# High-Performance Mode (Frame Skipping)
python visualize.py --flux 5e7 --steps-per-frame 20
```

**Visual Codes:**
- **Grey Grid**: Functional bits.
- **Yellow**: Latent Error (Masked). The system is vulnerable.
- **Red**: System Failure.
- **Fading Trails (Persistence)**: "Ghost" colors indicate where errors recently existed, highlighting hotspots even after corrections.

## 5. Directory Structure

```text
RadAnalysis/
├── src/
│   ├── core/       # Vectorized TMR Engine & Simulation Loop
│   ├── physics/    # Beam Interaction Models (Flux/Fluence)
│   ├── stats/      # Statistical Observers (Sliding Window, CI)
│   └── utils/      # Configuration Dataclasses
├── tests/          # Unit Verification
├── run_simulation.py  # Numerical Entry Point
└── visualize.py       # Graphical Entry Point
```
