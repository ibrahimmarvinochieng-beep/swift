"""Neo4j connection and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from neo4j import AsyncGraphDatabase, AsyncDriver
from app.core.config import get_settings


_driver: AsyncDriver | None = None


async def get_neo4j_driver() -> AsyncDriver:
    """Get or create Neo4j async driver."""
    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


@asynccontextmanager
async def get_session() -> AsyncGenerator:
    """Async context manager for Neo4j session."""
    driver = await get_neo4j_driver()
    async with driver.session() as session:
        yield session


async def close_neo4j():
    """Close Neo4j driver."""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None


async def init_neo4j_schema():
    """Create constraints and indexes."""

    async def _create_schema(tx):
        # Constraints
        await tx.run("CREATE CONSTRAINT loc_id IF NOT EXISTS FOR (n:Location) REQUIRE n.id IS UNIQUE")
        await tx.run("CREATE CONSTRAINT infra_id IF NOT EXISTS FOR (n:Infrastructure) REQUIRE n.id IS UNIQUE")
        await tx.run("CREATE CONSTRAINT ind_id IF NOT EXISTS FOR (n:Industry) REQUIRE n.id IS UNIQUE")
        await tx.run("CREATE CONSTRAINT org_id IF NOT EXISTS FOR (n:Organization) REQUIRE n.id IS UNIQUE")
        await tx.run("CREATE CONSTRAINT sc_id IF NOT EXISTS FOR (n:SupplyChain) REQUIRE n.id IS UNIQUE")
        # Indexes
        for label in ["Location", "Infrastructure", "Industry", "Organization", "SupplyChain"]:
            safe = label.lower()
            await tx.run(f"CREATE INDEX {safe}_name IF NOT EXISTS FOR (n:{label}) ON (n.name)")
            await tx.run(f"CREATE INDEX {safe}_type IF NOT EXISTS FOR (n:{label}) ON (n.type)")

    driver = await get_neo4j_driver()
    async with driver.session() as session:
        await session.execute_write(_create_schema)
