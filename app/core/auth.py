import logging
from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)


async def verify_auth(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
) -> str:
    """
    Dependency to verify API Key and Tenant ID headers.
    Returns the validated tenant ID on success.
    """
    if not settings.API_KEY or not settings.TENANT:
        logger.warning(
            "Authentication settings (API_KEY, TENANT) are not properly configured. "
            "Accepting request, but this is unsafe for production."
        )
        return x_tenant_id or "unknown"

    if (
        x_api_key == "demo-key"
        and x_tenant_id == "demo-tenant"
        and settings.API_KEY == "demo-key"
        and settings.TENANT == "demo-tenant"
    ):
        return x_tenant_id

    if x_api_key != settings.API_KEY or x_tenant_id != settings.TENANT:
        logger.warning(f"Unauthorized access attempt for tenant: {x_tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key or tenant"
        )

    return x_tenant_id
