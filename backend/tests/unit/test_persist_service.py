from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.db.repositories.artifact_repo import ArtifactRepository
from app.db.repositories.project_repo import ProjectRepository
from app.services.persist_service import PersistService
from app.services.storage_service import StorageService


@pytest.fixture
def persist_service():
    return PersistService()


@pytest.fixture
def mock_project_repo():
    repo = MagicMock(spec=ProjectRepository)
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_artifact_repo():
    repo = MagicMock(spec=ArtifactRepository)
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_storage():
    storage = MagicMock(spec=StorageService)
    return storage


@pytest.fixture
def sample_project_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_state() -> dict:
    return {
        "project_id": str(uuid4()),
        "status": "running",
        "idea": "Build a REST API",
        "requirements": {"title": "SRS"},
        "revision": 1,
        "token_usage": [
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300},
        ],
        "errors": [],
    }


STORAGE_PATH = "app.services.persist_service.storage_service"


class TestPersistService:
    @patch(STORAGE_PATH)
    async def test_persist_agent_output(
        self,
        mock_storage,
        persist_service,
        mock_project_repo,
        mock_artifact_repo,
        sample_project_id,
        sample_state,
    ):
        await persist_service.persist_agent_output(
            project_repo=mock_project_repo,
            artifact_repo=mock_artifact_repo,
            project_id=sample_project_id,
            agent_type="requirements",
            artifact_type="requirements_doc",
            content={"title": "SRS"},
            state=sample_state,
            revision=1,
        )

        mock_artifact_repo.create.assert_awaited_once_with(
            project_id=sample_project_id,
            agent_type="requirements",
            artifact_type="requirements_doc",
            content={"title": "SRS"},
            revision=1,
        )
        mock_storage.save_checkpoint.assert_called_once()

    @patch(STORAGE_PATH)
    async def test_persist_agent_output_uses_default_revision(
        self,
        _mock_storage,
        persist_service,
        mock_project_repo,
        mock_artifact_repo,
        sample_project_id,
        sample_state,
    ):
        await persist_service.persist_agent_output(
            project_repo=mock_project_repo,
            artifact_repo=mock_artifact_repo,
            project_id=sample_project_id,
            agent_type="developer",
            artifact_type="source_code",
            content={"files": []},
            state=sample_state,
        )

        mock_artifact_repo.create.assert_awaited_once_with(
            project_id=sample_project_id,
            agent_type="developer",
            artifact_type="source_code",
            content={"files": []},
            revision=1,
        )

    @patch(STORAGE_PATH)
    async def test_persist_generated_code(
        self,
        mock_storage,
        persist_service,
        sample_project_id,
    ):
        files = [
            {"path": "main.py", "content": "print('hello')", "language": "python"},
            {"path": "utils.py", "content": "def helper(): pass", "language": "python"},
        ]

        await persist_service.persist_generated_code(
            project_id=sample_project_id,
            files=files,
            revision=2,
        )

        mock_storage.save_generated_code.assert_called_once_with(
            project_id=str(sample_project_id),
            files=files,
            revision=2,
        )

    @patch(STORAGE_PATH)
    async def test_finalize_project_completed(
        self,
        mock_storage,
        persist_service,
        mock_project_repo,
        sample_project_id,
        sample_state,
    ):
        await persist_service.finalize_project(
            project_repo=mock_project_repo,
            project_id=sample_project_id,
            state=sample_state,
        )

        mock_project_repo.update.assert_awaited_once()
        assert mock_project_repo.update.call_args[0][0] == sample_project_id
        update_kwargs = mock_project_repo.update.call_args[1]
        assert str(update_kwargs["status"]) == "completed"

        mock_storage.save_checkpoint.assert_called_once()
        mock_storage.create_backup.assert_called_once()
        mock_storage.save_manifest.assert_called_once()

    @patch(STORAGE_PATH)
    async def test_finalize_project_failed(
        self,
        _mock_storage,
        persist_service,
        mock_project_repo,
        sample_project_id,
        sample_state,
    ):
        sample_state["errors"] = [{"step": "requirements", "message": "Failed"}]

        await persist_service.finalize_project(
            project_repo=mock_project_repo,
            project_id=sample_project_id,
            state=sample_state,
        )

        update_kwargs = mock_project_repo.update.call_args[1]
        assert str(update_kwargs["status"]) == "failed"

    @patch(STORAGE_PATH)
    async def test_finalize_project_failed_when_errors_none(
        self,
        _mock_storage,
        persist_service,
        mock_project_repo,
        sample_project_id,
        sample_state,
    ):
        sample_state["errors"] = None

        await persist_service.finalize_project(
            project_repo=mock_project_repo,
            project_id=sample_project_id,
            state=sample_state,
        )

        update_kwargs = mock_project_repo.update.call_args[1]
        assert str(update_kwargs["status"]) == "completed"

    def test_sum_tokens_empty(self, persist_service):
        result = persist_service._sum_tokens([])
        assert result == {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def test_sum_tokens_multiple_entries(self, persist_service):
        usage = [
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300},
        ]
        result = persist_service._sum_tokens(usage)
        assert result == {"prompt_tokens": 300, "completion_tokens": 150, "total_tokens": 450}

    def test_sum_tokens_handles_missing_keys(self, persist_service):
        usage = [
            {"prompt_tokens": 100, "total_tokens": 150},
            {"completion_tokens": 50},
        ]
        result = persist_service._sum_tokens(usage)
        assert result == {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}


class TestPersistServiceSingleton:
    def test_persist_service_is_singleton(self):
        from app.services.persist_service import persist_service

        assert persist_service is not None
        assert isinstance(persist_service, PersistService)
