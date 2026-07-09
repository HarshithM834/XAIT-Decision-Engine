import os
from typing import Optional
from fastapi import Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from app.core.config import settings
from app.core.logging import logger

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

azure_scheme = None
if settings.AZURE_TENANT_ID and settings.AZURE_CLIENT_ID:
    try:
        from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
        azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
            app_client_id=settings.AZURE_CLIENT_ID,
            tenant_id=settings.AZURE_TENANT_ID,
            scopes={
                f"api://{settings.AZURE_CLIENT_ID}/user_impersonation": "user_impersonation",
            }
        )
        logger.info("Azure AD Authentication initialized.")
    except ImportError:
        logger.warning("fastapi-azure-auth not installed but Azure settings present.")

async def get_api_key(request: Request, api_key: Optional[str] = Security(api_key_header)) -> str:
    if settings.DEV_MODE and os.getenv("DEV_MODE") == "true":
        if not api_key and not request.headers.get("Authorization"):
            return "dev_mode_key"

    # If Azure AD is configured, validate the token
    if azure_scheme and request.headers.get("Authorization"):
        try:
            token = await azure_scheme(request)
            # You can extract user details from the token here
            return token.get("preferred_username", "azure_user")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Azure AD token: {e}"
            )

    # Fallback to standard API Key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing API Key or Azure AD Token"
        )
        
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
        
    return api_key
