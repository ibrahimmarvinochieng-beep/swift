"""API endpoint tests. Run with: pytest tests/ -v"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_invalid_node_id_rejected(client):
    """IDs with invalid chars should be rejected (422)."""
    r = await client.post(
        "/nodes/",
        json={"id": "bad id!'", "type": "Location", "name": "Bad", "metadata": {}},
    )
    assert r.status_code == 422
