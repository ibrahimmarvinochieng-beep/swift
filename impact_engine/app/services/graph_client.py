"""Async HTTP client for Graph Service."""

import asyncio
import httpx
from app.core.config import get_settings


class GraphServiceError(Exception):
    pass


class GraphServiceClient:
    def __init__(self):
        s = get_settings()
        self.base_url = s.graph_service_url.rstrip("/")
        self.timeout = s.graph_timeout_seconds
        self.retries = s.graph_retry_attempts

    async def _request(self, method, path, params=None):
        url = self.base_url + path
        last_err = None
        for attempt in range(self.retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    r = await client.request(method, url, params=params)
                    r.raise_for_status()
                    return r.json() if r.content else {}
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_err = e
                if attempt < self.retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
        raise GraphServiceError(str(last_err))

    async def get_propagation_paths(self, node_id, max_depth=3, min_weight=0.0, limit=5000):
        return await self._request("GET", "/propagation-paths/" + node_id, params={"max_depth": max_depth, "min_weight": min_weight, "limit": limit})
