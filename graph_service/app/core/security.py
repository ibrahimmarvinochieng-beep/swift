"""API security: auth and rate limiting."""

from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)
limiter = Limiter(key_func=get_remote_address)


async def verify_api_key(api_key: Optional[str] = Depends(api_key_header)) -> Optional[str]:
    """Validate API key. Returns key if valid. Allows unauthenticated if no key configured."""
    settings = get_settings()
    if not settings.api_key:
        return None  # Dev mode: no auth required
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


async def optional_auth(
    api_key: Optional[str] = Depends(api_key_header),
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[str]:
    """Optional auth: accept API key or Bearer token."""
    if api_key:
        return await verify_api_key(api_key)
    if creds:
        # JWT validation would go here
        return creds.credentials
    return None
