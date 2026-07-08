from typing import Dict, Any, List
from app.jobs.base import BaseJobRunner
from app.jobs.email import EmailJobRunner
from app.core.logging import logger

class JobExecutor:
    def __init__(self):
        self.runners: Dict[str, BaseJobRunner] = {
            "send_email": EmailJobRunner()
        }

    def execute_jobs(self, actions: List[Dict[str, str]], payload: Dict[str, Any], decision_context: Dict[str, Any]) -> List[Dict[str, str]]:
        executed = []
        for action in actions:
            action_type = action.get("type")
            if not action_type or action_type == "none":
                continue
                
            runner = self.runners.get(action_type)
            if runner:
                try:
                    status = runner.execute(payload, decision_context)
                    executed.append({"job_type": action_type, "status": status})
                except Exception as e:
                    logger.error(f"Job execution failed for {action_type}", exc_info=True)
                    executed.append({"job_type": action_type, "status": "failed", "error": str(e)})
            else:
                logger.warning(f"No job runner found for action type: {action_type}")
                executed.append({"job_type": action_type, "status": "skipped", "error": "Runner not found"})
                
        return executed
