import logging
import json
import sys
from datetime import datetime, timezone
from app.core.config import settings

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info and settings.ENVIRONMENT == "development":
            log_data["exc_info"] = self.formatException(record.exc_info)
            
        if hasattr(record, "run_id"):
            log_data["run_id"] = record.run_id
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        # Mask secrets
        if "API_KEY" in log_data.get("message", ""):
            log_data["message"] = "API_KEY logged [MASKED]"

        return json.dumps(log_data)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)

    # Clear existing handlers
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    return logger

logger = setup_logging()
