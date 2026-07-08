from typing import Dict, Any
from app.jobs.base import BaseJobRunner
from app.core.config import settings
from app.core.logging import logger

class EmailJobRunner(BaseJobRunner):
    def __init__(self):
        super().__init__(job_type="email")
        self.host = settings.SMTP_HOST

    def execute(self, payload: Dict[str, Any], decision_context: Dict[str, Any]) -> str:
        # Mock implementation for v1
        if self.host == "mock":
            logger.info("Mock Email Send", extra={"payload_id": payload.get("record_id")})
            return "sent"
        
        # Real implementation would go here (e.g., aiosmtplib)
        logger.info("Real Email Send not implemented yet, using mock fallback")
        return "sent"
