"""Swift Event Intelligence Platform — FastAPI application.

On startup the app:
  1. Creates a default admin user
  2. Initialises the distributed token-bucket rate limiter (Redis or in-memory)
  3. (if PIPELINE_AUTOSTART=true) Launches a background pipeline loop

The API and pipeline share a single EventRepository so events appear
in the API as soon as they are processed.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

from api.routes import router
from api.auth import create_default_admin
from db.repository import event_repo
from rate_limiter.limiter import TokenBucketLimiter
from rate_limiter.middleware import TokenBucketMiddleware
from utils.config_loader import get_settings
from utils.logger import logger

settings = get_settings()

REQUEST_COUNT = Counter(
    "swift_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "swift_request_latency_seconds", "Request latency", ["endpoint"]
)

_pipeline_task: asyncio.Task = None
_rate_limiter: TokenBucketLimiter = None


def _build_rate_limiter() -> TokenBucketLimiter:
    """Create the token-bucket limiter, using Redis when available."""
    redis_client = None
    if settings.rate_limiter_use_redis:
        try:
            from streaming.redis_stream import get_redis
            redis_client = get_redis()
        except Exception as exc:
            logger.warning("redis_unavailable_for_limiter", error=str(exc))

    return TokenBucketLimiter(
        bucket_size=settings.rate_limiter_bucket_size,
        refill_rate=settings.rate_limiter_refill_rate,
        key_prefix=settings.rate_limiter_key_prefix,
        redis_client=redis_client,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pipeline_task, _rate_limiter

    logger.info("swift_starting", environment=settings.environment)
    create_default_admin()

    _rate_limiter = _build_rate_limiter()

    if settings.pipeline_autostart:
        from pipeline.orchestrator import start_pipeline_loop

        _pipeline_task = asyncio.create_task(
            start_pipeline_loop(interval_seconds=settings.pipeline_interval_seconds)
        )
        logger.info("pipeline_background_started")
    else:
        logger.info("pipeline_autostart_disabled")

    yield

    if _pipeline_task and not _pipeline_task.done():
        _pipeline_task.cancel()
        try:
            await _pipeline_task
        except asyncio.CancelledError:
            pass

    event_repo.close()
    logger.info("swift_shutting_down")


app = FastAPI(
    title="Swift Event Intelligence Platform",
    description=(
        "Real-time intelligence platform — Data Ingestion & Event Detection Engine.\n\n"
        "**Default credentials:** admin / SwiftAdmin2026!\n\n"
        "1. POST `/api/v1/auth/login` to get a JWT token\n"
        "2. Use the token as `Bearer <token>` in the Authorize dialog\n"
        "3. Browse `/api/v1/events` — events are seeded automatically on startup"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.environment == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*.swift.ai", "localhost"])


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    endpoint = request.url.path
    REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
    REQUEST_LATENCY.labels(endpoint).observe(duration)

    response.headers["X-Process-Time"] = str(round(duration, 4))
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"

    if settings.tls_enabled:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response


app.include_router(router)


@app.get("/health", tags=["System"])
async def health():
    stats = event_repo.get_stats()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "events_stored": stats["events_stored"],
        "pipeline_runs": stats["pipeline_runs"],
        "persistence": event_repo.backend,
        "tls": "enabled" if settings.tls_enabled else "disabled",
        "encryption_at_rest": "enabled" if settings.encrypt_sensitive_fields else "disabled",
        "rate_limiter": {
            "backend": "redis" if (_rate_limiter and _rate_limiter.is_distributed) else "in-memory",
            "bucket_size": settings.rate_limiter_bucket_size,
            "refill_rate": settings.rate_limiter_refill_rate,
        },
        "services": {
            "api": "up",
            "pipeline": "running" if (_pipeline_task and not _pipeline_task.done()) else "stopped",
            "database": "configured",
            "redis": "configured",
            "kafka": "configured",
        },
    }


@app.get("/metrics", tags=["System"])
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
