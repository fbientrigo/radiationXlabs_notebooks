from dataclasses import dataclass
from typing import Tuple

@dataclass
class SimulationConfig:
    """
    Configuration for the Radiation Analysis Simulation.

    Attributes:
        flux (float): Particle flux in particles/cm^2/s.
        sigma (float): Cross section in cm^2/device.
        scrubbing_interval (Tuple[float, float]): (Mean, StdDev) of the scrubbing interval in seconds.
        triad_count (int): Number of TMR triads in the chip geometry.
    """
    flux: float
    sigma: float
    scrubbing_interval: Tuple[float, float]
    triad_count: int
    
    # Burst/Spill Parameters (Defaults for Constant/DC Beam)
    flux_active: float = 0.0 # Peak flux during spill. If 0, uses 'flux'.
    flux_background: float = 0.0 # Background flux between spills.
    duty_cycle: float = 1.0 # Fraction of time ON (0.0 to 1.0).
    spill_duration: float = 1.0 # Duration of the ON phase in seconds.

    @property
    def lambda_theory_device(self) -> float:
        """
        Calculates theoretical failure rate per device.
        lambda = Flux * Sigma
        """
        return self.flux * self.sigma

    @property
    def lambda_theory_total(self) -> float:
        """
        Calculates theoretical failure rate for the entire system (all triads).
        Assuming independent failures: lambda_total = lambda_device * 3 * triad_count
        (Note: TMR logic might differ, this is raw upset rate).
        """
        # Raw upset rate for the whole chip (3 ffs per triad)
        return self.lambda_theory_device * 3 * self.triad_count
