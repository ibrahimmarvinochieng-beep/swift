"""FastAPI Graph Service entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import nodes, edges, queries
from app.db.neo4j import init_neo4j_schema, close_neo4j
from app.core.security import limiter, verify_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_neo4j_schema()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Neo4j schema init failed (Neo4j may be down): %s", e)
    yield
    await close_neo4j()


app = FastAPI(
    title="Swift Dependency Graph Service",
    description="Real-time world model of dependencies for impact prediction and simulation",
    version="1.0.0",
    lifespan=lifespan,
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

app.include_router(nodes.router, dependencies=[Depends(verify_api_key)])
app.include_router(edges.router, dependencies=[Depends(verify_api_key)])
app.include_router(queries.router, dependencies=[Depends(verify_api_key)])


@app.get("/health")
async def health():
    return {"status": "ok"}
