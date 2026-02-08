from typing import Dict, Any
from ..physics.beam import ParticleBeam
from .tmr_system import TMRSystem
from ..stats.observer import StatisticsObserver
from ..utils.config import SimulationConfig

class SimulationEngine:
    def __init__(self, config: SimulationConfig, beam: ParticleBeam, tmr: TMRSystem, observer: StatisticsObserver):
        self.config = config
        self.beam = beam
        self.tmr = tmr
        self.observer = observer
        
        self.current_time = 0.0
        self.total_fluence = 0.0

    def step(self, dt: float) -> Dict[str, Any]:
        self.current_time += dt
        
        # 1. Physics: Beam Generation (Time Dependent Flux)
        # Using instantaneous flux at current time for Euler step
        # (Assuming dt is small enough to capture structure)
        instant_flux = self.beam.get_flux_at(self.current_time)
        step_fluence = instant_flux * dt
        self.total_fluence += step_fluence
        
        # Update TMR and get New Upsets (SEUs)
        new_upsets, sys_failures, masked_errors = self.tmr.update_state(step_fluence, dt)
        
        # Record each new upset as a statistical event
        # (This aligns "Lambda Observed" with "Lambda Theory" = Flux * Sigma)
        for _ in range(new_upsets):
            self.observer.record_event(self.current_time, "fail")
            
        did_scrub = self.tmr.perform_scrubbing(self.current_time)
        
        return {
            "time": self.current_time,
            "fluence": self.total_fluence,
            "new_upsets": new_upsets,
            "sys_failures": sys_failures,
            "masked_errors": masked_errors,
            "did_scrub": did_scrub
        }

    def get_metrics(self) -> Dict[str, Any]:
        return self.observer.get_metrics(self.current_time)
