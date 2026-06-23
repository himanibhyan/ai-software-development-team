from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.server import app
from app.core.exceptions import AppException


@pytest.mark.asyncio
class TestServer:
    async def test_health_check(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "name" in data
        assert "version" in data

    async def test_exception_handler_returns_json(self):
        @app.get("/_test_raise_error")
        async def _raise():
            raise AppException(status_code=422, message="test detail", details="extra info")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/_test_raise_error")
        assert response.status_code == 422
        data = response.json()
        assert data["detail"] == "test detail"
        assert data["errors"] == ["extra info"]

        app.router.routes = [r for r in app.router.routes if r.path != "/_test_raise_error"]
