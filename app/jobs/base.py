from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseJobRunner(ABC):
    def __init__(self, job_type: str):
        self.job_type = job_type

    @abstractmethod
    def execute(self, payload: Dict[str, Any], decision_context: Dict[str, Any]) -> str:
        """
        Executes the job and returns a status string (e.g., 'sent', 'skipped', 'failed')
        """
        pass
