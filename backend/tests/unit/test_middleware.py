from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.middleware import register_middleware


@pytest.mark.asyncio
class TestMiddleware:
    async def test_request_logging_middleware_adds_process_time_header(self):
        test_app = FastAPI()

        @test_app.get("/ping")
        async def ping():
            return {"ok": True}

        register_middleware(test_app)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ping")

        assert response.status_code == 200
        assert "X-Process-Time-Ms" in response.headers

    async def test_register_middleware_does_not_crash(self):
        test_app = FastAPI()

        @test_app.get("/test")
        async def test_route():
            return {"msg": "hello"}

        register_middleware(test_app)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert response.status_code == 200
        assert response.json() == {"msg": "hello"}
