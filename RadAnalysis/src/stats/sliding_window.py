import math
from collections import deque
from typing import Dict, Any, Tuple
from ..utils.config import SimulationConfig
from .observer import StatisticsObserver

class SlidingWindowStats(StatisticsObserver):
    """
    Concrete implementation of StatisticsObserver using a sliding window approach.
    
    Calculates failure rates and statistics based on events occurring within 
    a specified time window T.
    """

    def __init__(self, config: SimulationConfig, window_size: float = 1.0):
        """
        Initialize the SlidingWindowStats observer.

        Args:
            config (SimulationConfig): Global simulation configuration.
            window_size (float): Size of the sliding window in seconds.
        """
        self.config = config
        self.window_size = window_size
        self.events = deque()  # Stores timestamps of events
        self.total_events = 0

    def record_event(self, timestamp: float, event_type: str = "fail") -> None:
        """
        Record a failure event.
        
        Args:
            timestamp (float): Time of the event.
            event_type (str): Type of event. Only 'fail' events are counted for lambda.
        """
        if event_type == "fail":
            self.events.append(timestamp)
            self.total_events += 1

    def _prune_old_events(self, current_time: float):
        """
        Remove events that are outside the current sliding window.
        """
        threshold = current_time - self.window_size
        while self.events and self.events[0] < threshold:
            self.events.popleft()

    def get_metrics(self, current_time: float) -> Dict[str, Any]:
        """
        Calculate statistical metrics for the current window.

        Metrics:
        - lambda_obs: Observed failure rate (events / window_size).
        - lambda_theory: Theoretical failure rate from config.
        - error_rel: Relative error between observed and theoretical.
        - ci_95: 95% Confidence Interval for lambda_obs (Poisson).
        - convergence: Indicator of statistical stability (1 / sqrt(N)).

        Args:
            current_time (float): Current simulation time.

        Returns:
            Dict[str, Any]: Dictionary of calculated metrics.
        """
        self._prune_old_events(current_time)
        
        k = len(self.events) # Number of events in window
        
        # Avoid division by zero if window is effectively 0 (start of sim)
        effective_window = min(current_time, self.window_size)
        if effective_window <= 0:
            return {
                "lambda_obs": 0.0,
                "lambda_theory": self.config.lambda_theory_total,
                "error_rel": 0.0,
                "ci_95": (0.0, 0.0),
                "convergence": 0.0,
                "events_in_window": 0,
                "total_events": self.total_events
            }

        # Lambda Observed
        lambda_obs = k / effective_window

        # Lambda Theory
        lambda_theory = self.config.lambda_theory_total

        # Relative Error
        error_rel = abs(lambda_obs - lambda_theory) / lambda_theory if lambda_theory > 0 else 0.0

        # Confidence Interval (Poisson approximation: lambda +/- 1.96 * sqrt(lambda/T))
        # Standard Error of rate = sqrt(lambda / T) = sqrt(k/T^2) = sqrt(k)/T
        # Margin of Error = 1.96 * SE
        se = math.sqrt(k) / effective_window
        margin = 1.96 * se
        ci_lower = max(0.0, lambda_obs - margin)
        ci_upper = lambda_obs + margin

        # Convergence metric (1/sqrt(N) is proportional to relative statistical error)
        # Using total accumulated events for long-term convergence, or window events for local stability
        # Typically convergence refers to the long-term estimate. 
        # Here we return local stability metric based on window count.
        convergence = 1.0 / math.sqrt(k) if k > 0 else 1.0

        return {
            "lambda_obs": lambda_obs,
            "lambda_theory": lambda_theory,
            "error_rel": error_rel,
            "ci_95": (ci_lower, ci_upper),
            "convergence": convergence,
            "events_in_window": k,
            "total_events": self.total_events
        }

    def reset(self) -> None:
        """Reset the observer."""
        self.events.clear()
        self.total_events = 0
