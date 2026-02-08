import numpy as np
import math
from typing import Tuple, List
from ..utils.config import SimulationConfig

class TMRSystem:
    """
    Simulates a Triple Modular Redundancy (TMR) Digital System.
    Uses NumPy for efficient vectorized bit-flip simulation.
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.n_triads = config.triad_count
        self.bits = np.zeros((self.n_triads, 3), dtype=np.int8)
        self.masked_count = 0
        self.failure_count = 0
        self.next_scrub_time = self._get_next_scrub_interval()

    def _get_next_scrub_interval(self) -> float:
        mean, std = self.config.scrubbing_interval
        interval = np.random.normal(mean, std)
        return max(1e-6, interval)

    def update_state(self, fluence: float, dt: float) -> Tuple[int, int, int]:
        """
        Apply radiation effects.
        Returns: (New Upsets, Total Failures, Total Masked)
        """
        if fluence <= 0:
            return (0, self.failure_count, self.masked_count)

        prob_flip = 1.0 - np.exp(-self.config.sigma * fluence)
        
        rng = np.random.random(self.bits.shape)
        flips = rng < prob_flip # Boolean mask of NEW flips
        n_flips = np.sum(flips)
        
        self.bits[flips] = 1 - self.bits[flips] # Toggle

        # Recalculate System State
        upsets_per_triad = np.sum(self.bits, axis=1)
        self.masked_count = np.sum(upsets_per_triad == 1)
        self.failure_count = np.sum(upsets_per_triad >= 2)
        
        return (n_flips, self.failure_count, self.masked_count)

    def perform_scrubbing(self, current_time: float) -> bool:
        if current_time >= self.next_scrub_time:
            self.bits.fill(0)
            self.masked_count = 0
            self.failure_count = 0
            self.next_scrub_time = current_time + self._get_next_scrub_interval()
            return True
        return False
