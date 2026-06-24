from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "name" in data
        assert "version" in data


@pytest.mark.asyncio
class TestProjectAPI:
    async def test_create_project(self, client: AsyncClient, sample_idea: str):
        response = await client.post(
            "/api/v1/projects",
            json={"idea": sample_idea},
        )
        assert response.status_code == 201
        data = response.json()
        assert "project_id" in data
        assert data["status"] == "pending"

    async def test_create_project_validation_error(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/projects",
            json={"idea": "short"},
        )
        assert response.status_code == 422

    async def test_get_project_not_found(self, client: AsyncClient):
        response = await client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    async def test_list_projects(self, client: AsyncClient):
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    async def test_create_and_get_project(self, client: AsyncClient, sample_idea: str):
        create_resp = await client.post(
            "/api/v1/projects",
            json={"idea": sample_idea},
        )
        assert create_resp.status_code == 201
        project_id = create_resp.json()["project_id"]

        get_resp = await client.get(f"/api/v1/projects/{project_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["id"] == project_id
        assert data["idea"] == sample_idea

    async def test_create_and_get_status(self, client: AsyncClient, sample_idea: str):
        create_resp = await client.post(
            "/api/v1/projects",
            json={"idea": sample_idea},
        )
        project_id = create_resp.json()["project_id"]

        status_resp = await client.get(f"/api/v1/projects/{project_id}/status")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["project_id"] == project_id
        assert data["status"] in ("pending", "running", "completed", "failed")

    async def test_list_projects_pagination(self, client: AsyncClient, _sample_idea: str):
        resp = await client.get("/api/v1/projects?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    async def test_delete_project_not_found(self, client: AsyncClient):
        response = await client.delete("/api/v1/projects/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
