"""API security."""

from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
limiter = Limiter(key_func=get_remote_address)


async def verify_api_key(api_key: Optional[str] = Depends(api_key_header)) -> Optional[str]:
    s = get_settings()
    if not s.api_key:
        return None
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if api_key != s.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
