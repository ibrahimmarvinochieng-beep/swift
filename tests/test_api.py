"""Tests for the FastAPI application endpoints."""

import os
os.environ["PIPELINE_AUTOSTART"] = "false"

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.auth import create_default_admin

create_default_admin()
client = TestClient(app, raise_server_exceptions=False)


def _admin_token() -> str:
    r = client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "SwiftAdmin2026!",
    })
    return r.json()["access_token"]


def _auth_header(token: str = None) -> dict:
    return {"Authorization": f"Bearer {token or _admin_token()}"}


# ── System ────────────────────────────────────────────────────────────

class TestSystem:
    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "events_stored" in data

    def test_docs(self):
        assert client.get("/docs").status_code == 200

    def test_metrics(self):
        assert client.get("/metrics").status_code == 200


# ── Auth ──────────────────────────────────────────────────────────────

class TestAuth:
    def test_register(self):
        r = client.post("/api/v1/auth/register", json={
            "username": "testuser_api",
            "email": "testapi@swift.ai",
            "password": "TestPass123!",
            "role": "analyst",
        })
        assert r.status_code == 200
        assert r.json()["username"] == "testuser_api"

    def test_register_duplicate(self):
        client.post("/api/v1/auth/register", json={
            "username": "dup_user",
            "email": "dup@swift.ai",
            "password": "TestPass123!",
        })
        r = client.post("/api/v1/auth/register", json={
            "username": "dup_user",
            "email": "dup2@swift.ai",
            "password": "TestPass123!",
        })
        assert r.status_code == 400

    def test_login_success(self):
        client.post("/api/v1/auth/register", json={
            "username": "login_user",
            "email": "login@swift.ai",
            "password": "TestPass123!",
        })
        r = client.post("/api/v1/auth/login", json={
            "username": "login_user",
            "password": "TestPass123!",
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_failure(self):
        r = client.post("/api/v1/auth/login", json={
            "username": "nobody", "password": "wrong",
        })
        assert r.status_code == 401

    def test_protected_endpoint_requires_auth(self):
        r = client.get("/api/v1/events")
        assert r.status_code in [401, 403]


# ── Events ────────────────────────────────────────────────────────────

class TestEvents:
    def test_list_events(self):
        r = client.get("/api/v1/events", headers=_auth_header())
        assert r.status_code == 200
        data = r.json()
        assert "events" in data
        assert "total" in data
        assert "page" in data

    def test_event_not_found(self):
        r = client.get("/api/v1/events/nonexistent-id", headers=_auth_header())
        assert r.status_code == 404

    def test_event_type_summary(self):
        r = client.get("/api/v1/events/types/summary", headers=_auth_header())
        assert r.status_code == 200
        assert "types" in r.json()


# ── Ingestion ─────────────────────────────────────────────────────────

class TestIngestion:
    def test_ingest_event_signal(self):
        r = client.post("/api/v1/ingest", headers=_auth_header(), json={
            "content": "A massive earthquake of magnitude 7.1 struck central Turkey causing widespread destruction and building collapses",
            "source_type": "manual",
            "source_name": "test",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] in ["accepted", "rejected"]

    def test_ingest_batch(self):
        r = client.post("/api/v1/ingest/batch", headers=_auth_header(), json={
            "signals": [
                {"content": "Severe flooding in Bangladesh displaces millions as rivers overflow during monsoon season", "source_type": "manual"},
                {"content": "Major power outage across Texas leaves 4 million homes without electricity in winter storm emergency", "source_type": "manual"},
            ],
        })
        assert r.status_code == 200
        data = r.json()
        assert "accepted" in data
        assert "rejected" in data

    def test_ingest_requires_analyst_role(self):
        client.post("/api/v1/auth/register", json={
            "username": "viewer_only",
            "email": "viewer@swift.ai",
            "password": "TestPass123!",
            "role": "viewer",
        })
        r = client.post("/api/v1/auth/login", json={
            "username": "viewer_only",
            "password": "TestPass123!",
        })
        token = r.json()["access_token"]

        r = client.post("/api/v1/ingest", headers=_auth_header(token), json={
            "content": "A massive earthquake struck central Turkey causing widespread destruction and emergency response",
            "source_type": "manual",
        })
        assert r.status_code == 403


# ── Pipeline ──────────────────────────────────────────────────────────

class TestPipeline:
    def test_pipeline_status(self):
        r = client.get("/api/v1/pipeline/status", headers=_auth_header())
        assert r.status_code == 200
        data = r.json()
        assert "events_stored" in data
        assert "uptime_seconds" in data
        assert "collector_status" in data
