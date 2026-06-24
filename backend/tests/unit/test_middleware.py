from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.config import settings
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


@pytest.mark.asyncio
class TestRateLimitMiddleware:
    @pytest.fixture(autouse=True)
    def patch_env(self):
        with patch.object(settings, "ENVIRONMENT", "development"), \
             patch.object(settings, "RATE_LIMIT_REQUESTS", 3), \
             patch.object(settings, "RATE_LIMIT_WINDOW_SECONDS", 60):
            yield

    async def test_under_limit_passes(self):
        test_app = FastAPI()

        @test_app.get("/test")
        async def test_route():
            return {"ok": True}

        register_middleware(test_app)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(3):
                response = await client.get("/test")
                assert response.status_code == 200
                assert response.json() == {"ok": True}

    async def test_returns_429_when_limit_exceeded(self):
        test_app = FastAPI()

        @test_app.get("/test")
        async def test_route():
            return {"ok": True}

        register_middleware(test_app)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(3):
                await client.get("/test")

            response = await client.get("/test")
            assert response.status_code == 429
            assert response.json()["detail"] == "Rate limit exceeded. Try again later."

    async def test_rate_limit_headers_present(self):
        test_app = FastAPI()

        @test_app.get("/test")
        async def test_route():
            return {"ok": True}

        register_middleware(test_app)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")
            assert response.headers.get("X-RateLimit-Limit") == "3"
            assert response.headers.get("X-RateLimit-Remaining") == "2"
            assert "X-RateLimit-Reset" in response.headers

    async def test_rate_limit_resets_after_window(self):
        test_app = FastAPI()

        @test_app.get("/test")
        async def test_route():
            return {"ok": True}

        register_middleware(test_app)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(3):
                await client.get("/test")

            response = await client.get("/test")
            assert response.status_code == 429

        # Create a new app (new timer window) to simulate reset
        test_app2 = FastAPI()

        @test_app2.get("/test")
        async def test_route2():
            return {"ok": True}

        register_middleware(test_app2)

        transport2 = ASGITransport(app=test_app2)
        async with AsyncClient(transport=transport2, base_url="http://test") as client2:
            response = await client2.get("/test")
            assert response.status_code == 200

    async def test_skipped_in_test_environment(self):
        with patch.object(settings, "ENVIRONMENT", "test"):
            test_app = FastAPI()

            @test_app.get("/test")
            async def test_route():
                return {"ok": True}

            register_middleware(test_app)

            transport = ASGITransport(app=test_app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                for _ in range(10):
                    response = await client.get("/test")
                    assert response.status_code == 200

    async def test_zero_remaining_when_blocked(self):
        test_app = FastAPI()

        @test_app.get("/test")
        async def test_route():
            return {"ok": True}

        register_middleware(test_app)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for _ in range(3):
                await client.get("/test")

            response = await client.get("/test")
            assert response.headers.get("X-RateLimit-Remaining") == "0"
