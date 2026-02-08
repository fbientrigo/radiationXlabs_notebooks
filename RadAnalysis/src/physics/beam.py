import numpy as np

import numpy as np

class ParticleBeam:
    """
    Base class for a particle beam. 
    Maintains compatibility but encourages use of subclasses.
    """
    def __init__(self, flux_nominal: float):
        self.flux_nominal = flux_nominal

    def get_flux_at(self, time: float) -> float:
        """Returns instantaneous flux at time t."""
        return self.flux_nominal

    def get_fluence(self, dt: float) -> float:
        """Deprecated: Use engine integration instead."""
        return self.flux_nominal * dt

class BurstBeam(ParticleBeam):
    """
    Models a Bursty/Spill-based particle beam.
    
    Physics:
        Cycle Period (T_cycle) = Spill Duration / Duty Cycle
        Active Phase: 0 <= t < Spill Duration -> Flux = Flux Active
        Passive Phase: Spill Duration <= t < T_cycle -> Flux = Flux Background
    """
    def __init__(self, flux_active: float, duty_cycle: float, spill_duration: float, flux_background: float = 0.0):
        """
        Args:
            flux_active (float): Peak flux during the spill (particles/cm^2/s).
            duty_cycle (float): Fraction of time beam is ON (0 < dc <= 1).
            spill_duration (float): Duration of the active spill phase (s).
            flux_background (float): Flux during the OFF phase (s).
        """
        super().__init__(flux_active)
        self.flux_active = flux_active
        self.flux_background = flux_background
        self.duty_cycle = max(1e-6, min(1.0, duty_cycle))
        self.spill_duration = max(1e-9, spill_duration)
        
        # Derived
        self.cycle_period = self.spill_duration / self.duty_cycle

    def get_flux_at(self, time: float) -> float:
        """
        Calculate instantaneous flux based on spill structure.
        """
        if self.duty_cycle >= 1.0:
            return self.flux_active

        # Phase in cycle
        t_mod = time % self.cycle_period
        
        if t_mod < self.spill_duration:
            return self.flux_active
        else:
            return self.flux_background
