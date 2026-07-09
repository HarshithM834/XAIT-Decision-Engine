import smtplib
from email.message import EmailMessage
from typing import Dict, Any
from app.jobs.base import BaseJobRunner
from app.core.config import settings
from app.core.logging import logger

class EmailJobRunner(BaseJobRunner):
    def __init__(self):
        super().__init__(job_type="email")
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.sender = settings.EMAIL_FROM

    def execute(self, payload: Dict[str, Any], decision_context: Dict[str, Any]) -> str:
        # Mock implementation for v1 or fallback
        if self.host == "mock" or not self.host:
            logger.info("Mock Email Send", extra={"payload_id": payload.get("record_id")})
            return "sent"
        
        try:
            msg = EmailMessage()
            msg.set_content(f"Action required for quote: {payload.get('record_id')}\\n\\nDetails: {decision_context}")
            msg["Subject"] = f"Action Required: Deal {payload.get('record_id')} Pending Approval"
            msg["From"] = self.sender
            msg["To"] = "approvals@example.com" # Ideally driven by config or rule actions

            # Connect to SMTP Server
            server = smtplib.SMTP(self.host, self.port)
            server.starttls()
            if self.user and self.password:
                server.login(self.user, self.password)
            server.send_message(msg)
            server.quit()
            logger.info("Real Email Sent Successfully", extra={"payload_id": payload.get("record_id")})
            return "sent"
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            # Fallback to failing the job gracefully
            return "failed"
