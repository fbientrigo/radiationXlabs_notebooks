from abc import ABC, abstractmethod
from typing import Any, Dict

class StatisticsObserver(ABC):
    """
    Abstract Base Class for statistical observers in the simulation.
    
    Observers are responsible for tracking events (failures, upsets) and 
    calculating statistical metrics over time.
    """

    @abstractmethod
    def record_event(self, timestamp: float, event_type: str = "fail") -> None:
        """
        Record a discrete event.

        Args:
            timestamp (float): The simulation time when the event occurred.
            event_type (str): Type of event (e.g., 'fail', 'upset').
        """
        pass

    @abstractmethod
    def get_metrics(self, current_time: float) -> Dict[str, Any]:
        """
        Calculate and return current statistical metrics.

        Args:
            current_time (float): Current simulation time.

        Returns:
            Dict[str, Any]: A dictionary containing calculated metrics 
                            (e.g., lambda_obs, error, confidence_interval).
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the observer state.
        """
        pass
