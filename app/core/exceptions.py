from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger

class EngineException(Exception):
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code

async def engine_exception_handler(request: Request, exc: EngineException) -> JSONResponse:
    # Attempt to grab correlation_id if it was set on request state
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.error(
        f"Engine error: {exc.code} - {exc.message}",
        extra={"correlation_id": correlation_id, "details": exc.details}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "correlation_id": correlation_id
            }
        },
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    logger.error(
        f"Unhandled server error: {str(exc)}",
        extra={"correlation_id": correlation_id},
        exc_info=exc
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected internal error occurred.",
                "correlation_id": correlation_id
            }
        },
    )
