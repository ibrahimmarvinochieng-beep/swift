"""Tests for the distributed token-bucket rate limiter.

All tests use the in-memory backend so they run without Redis.
"""

import time
import pytest
from fastapi.testclient import TestClient

from rate_limiter.limiter import TokenBucketLimiter, RateLimitResult
from rate_limiter.middleware import TokenBucketMiddleware


# ── Core limiter logic ────────────────────────────────────────────

class TestTokenBucketLimiter:
    def _make_limiter(self, bucket_size=5, refill_rate=1.0):
        return TokenBucketLimiter(
            bucket_size=bucket_size,
            refill_rate=refill_rate,
            redis_client=None,
        )

    def test_first_request_allowed(self):
        lim = self._make_limiter()
        r = lim.consume("user-1")
        assert r.allowed is True
        assert r.remaining_tokens == 4.0

    def test_bucket_drains(self):
        lim = self._make_limiter(bucket_size=3)
        for _ in range(3):
            r = lim.consume("drain-user")
            assert r.allowed is True

        r = lim.consume("drain-user")
        assert r.allowed is False
        assert r.retry_after > 0

    def test_different_users_isolated(self):
        lim = self._make_limiter(bucket_size=2)
        lim.consume("alice")
        lim.consume("alice")
        r_alice = lim.consume("alice")
        assert r_alice.allowed is False

        r_bob = lim.consume("bob")
        assert r_bob.allowed is True

    def test_refill_over_time(self):
        lim = self._make_limiter(bucket_size=2, refill_rate=1000.0)
        lim.consume("refill-user")
        lim.consume("refill-user")
        r = lim.consume("refill-user")
        assert r.allowed is False

        time.sleep(0.01)

        r = lim.consume("refill-user")
        assert r.allowed is True

    def test_refill_capped_at_bucket_size(self):
        lim = self._make_limiter(bucket_size=3, refill_rate=10000.0)
        time.sleep(0.01)

        r = lim.consume("cap-user")
        assert r.allowed is True
        assert r.remaining_tokens <= 3.0

    def test_retry_after_calculation(self):
        lim = self._make_limiter(bucket_size=1, refill_rate=2.0)
        lim.consume("retry-user")
        r = lim.consume("retry-user")
        assert r.allowed is False
        assert 0.0 < r.retry_after <= 1.0

    def test_consume_multiple_tokens(self):
        lim = self._make_limiter(bucket_size=10, refill_rate=1.0)
        r = lim.consume("multi-user", tokens=5)
        assert r.allowed is True
        assert r.remaining_tokens == 5.0

        r = lim.consume("multi-user", tokens=6)
        assert r.allowed is False

    def test_is_distributed_false_without_redis(self):
        lim = self._make_limiter()
        assert lim.is_distributed is False


# ── Middleware integration ────────────────────────────────────────

class TestMiddleware:
    """Test the middleware via FastAPI TestClient (in-memory limiter)."""

    @staticmethod
    def _make_app(bucket_size=3, refill_rate=0.1):
        from fastapi import FastAPI

        limiter = TokenBucketLimiter(
            bucket_size=bucket_size,
            refill_rate=refill_rate,
            redis_client=None,
        )

        test_app = FastAPI()
        test_app.add_middleware(TokenBucketMiddleware, limiter=limiter)

        @test_app.get("/health")
        async def health():
            return {"ok": True}

        @test_app.get("/api/test")
        async def test_endpoint():
            return {"data": "hello"}

        return test_app

    def test_exempt_paths_not_limited(self):
        app = self._make_app(bucket_size=1)
        client = TestClient(app)
        for _ in range(10):
            r = client.get("/health")
            assert r.status_code == 200

    def test_rate_limit_headers_present(self):
        app = self._make_app(bucket_size=10)
        client = TestClient(app)
        r = client.get("/api/test")
        assert r.status_code == 200
        assert "X-RateLimit-Limit" in r.headers
        assert "X-RateLimit-Remaining" in r.headers

    def test_429_after_exhaustion(self):
        app = self._make_app(bucket_size=2, refill_rate=0.001)
        client = TestClient(app)

        assert client.get("/api/test").status_code == 200
        assert client.get("/api/test").status_code == 200

        r = client.get("/api/test")
        assert r.status_code == 429
        assert "Retry-After" in r.headers
        assert int(r.headers["Retry-After"]) > 0
        body = r.json()
        assert body["detail"] == "Too Many Requests"
        assert "retry_after" in body

    def test_429_returns_correct_limit_header(self):
        app = self._make_app(bucket_size=1, refill_rate=0.001)
        client = TestClient(app)
        client.get("/api/test")
        r = client.get("/api/test")
        assert r.status_code == 429
        assert r.headers["X-RateLimit-Limit"] == "1"
        assert r.headers["X-RateLimit-Remaining"] == "0"

    def test_user_identified_by_jwt(self):
        """Authenticated users are identified by JWT 'sub' claim."""
        from utils.security_utils import create_access_token

        app = self._make_app(bucket_size=2, refill_rate=0.001)
        client = TestClient(app)

        token_a = create_access_token({"sub": "alice", "role": "admin"})
        token_b = create_access_token({"sub": "bob", "role": "admin"})

        client.get("/api/test", headers={"Authorization": f"Bearer {token_a}"})
        client.get("/api/test", headers={"Authorization": f"Bearer {token_a}"})
        r = client.get("/api/test", headers={"Authorization": f"Bearer {token_a}"})
        assert r.status_code == 429

        r = client.get("/api/test", headers={"Authorization": f"Bearer {token_b}"})
        assert r.status_code == 200

    def test_user_identified_by_header(self):
        """X-User-ID header is used when no JWT is present."""
        app = self._make_app(bucket_size=1, refill_rate=0.001)
        client = TestClient(app)

        client.get("/api/test", headers={"X-User-ID": "gateway-user-1"})
        r = client.get("/api/test", headers={"X-User-ID": "gateway-user-1"})
        assert r.status_code == 429

        r = client.get("/api/test", headers={"X-User-ID": "gateway-user-2"})
        assert r.status_code == 200
