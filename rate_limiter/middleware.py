"""FastAPI middleware that enforces the distributed token-bucket rate limit.

User identification priority:
  1. ``user_id`` from JWT payload (``sub`` claim) — authenticated requests
  2. ``X-User-ID`` header — pre-authenticated gateway traffic
  3. Client IP address — anonymous / unauthenticated fallback

When a request exceeds the limit, the middleware returns:
  - **429 Too Many Requests**
  - ``Retry-After`` header (seconds until the bucket refills enough)
  - ``X-RateLimit-Limit``, ``X-RateLimit-Remaining`` headers on every response
"""

import math
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from rate_limiter.limiter import TokenBucketLimiter
from utils.security_utils import decode_access_token
from utils.logger import logger

EXEMPT_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}


class TokenBucketMiddleware(BaseHTTPMiddleware):
    """Starlette middleware wrapping :class:`TokenBucketLimiter`."""

    def __init__(self, app: ASGIApp, limiter: TokenBucketLimiter):
        super().__init__(app)
        self.limiter = limiter

    # ── Identify the caller ───────────────────────────────────────

    @staticmethod
    def _extract_user_id(request: Request) -> str:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:]
            payload = decode_access_token(token)
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"

        header_id = request.headers.get("x-user-id")
        if header_id:
            return f"user:{header_id}"

        client = request.client
        return f"ip:{client.host}" if client else "ip:unknown"

    # ── Middleware entry point ─────────────────────────────────────

    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        user_id = self._extract_user_id(request)
        result = self.limiter.consume(user_id)

        if not result.allowed:
            retry_after = math.ceil(result.retry_after)
            logger.warning(
                "rate_limit_exceeded",
                user=user_id,
                retry_after=retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too Many Requests",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.limiter.bucket_size),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(self.limiter.bucket_size)
        response.headers["X-RateLimit-Remaining"] = str(int(result.remaining_tokens))
        return response
