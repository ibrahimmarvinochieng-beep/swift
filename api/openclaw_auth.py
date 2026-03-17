"""API key auth for OpenClaw alerts endpoint."""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from utils.config_loader import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_openclaw_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify OPENCLAW_ALERT_KEY. Used for /api/v1/alerts."""
    settings = get_settings()
    if not settings.openclaw_alert_key:
        raise HTTPException(status_code=503, detail="Alerts API not configured")
    if not api_key or api_key != settings.openclaw_alert_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key
