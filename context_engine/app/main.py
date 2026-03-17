"""Swift Personal Context Engine - FastAPI entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import feed, users, interactions
from app.db.database import init_db
from app.core.security import limiter, verify_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("DB init failed: %s", e)
    yield


app = FastAPI(title="Swift Personal Context Engine", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(users.router, dependencies=[Depends(verify_api_key)])
app.include_router(interactions.router, dependencies=[Depends(verify_api_key)])
app.include_router(feed.router, dependencies=[Depends(verify_api_key)])


@app.get("/health")
async def health():
    return {"status": "ok"}
