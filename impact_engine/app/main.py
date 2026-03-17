"""Impact Simulation Engine - FastAPI entrypoint."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.simulate import router as simulate_router
from app.core.security import limiter, verify_api_key

app = FastAPI(
    title="Swift Impact Simulation Engine",
    description="Probabilistic cascading impact engine for global-scale Agentic AI",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulate_router, dependencies=[Depends(verify_api_key)])


@app.get("/health")
async def health():
    return {"status": "ok"}
