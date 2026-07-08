import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    if settings.DEV_MODE and os.getenv("DEV_MODE") == "true":
        # Allow bypass in explicitly configured dev mode if no key provided
        if not api_key:
            return "dev_mode_key"
            
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing API Key"
        )
        
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
        
    return api_key
