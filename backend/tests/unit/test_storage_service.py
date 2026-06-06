from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.services.storage_service import (
    BACKUPS_DIR,
    CHECKPOINTS_DIR,
    STORAGE_DIR,
    StorageService,
    storage_service,
)


def _clean_dir(directory):
    """Remove all files from a directory tree."""
    if directory.exists():
        for f in directory.rglob("*"):
            if f.is_file():
                f.unlink()


@pytest.fixture(autouse=True)
def clean_storage():
    """Clean storage directories before and after each test."""
    for d in (STORAGE_DIR, CHECKPOINTS_DIR, BACKUPS_DIR):
        _clean_dir(d)
    yield
    for d in (STORAGE_DIR, CHECKPOINTS_DIR, BACKUPS_DIR):
        _clean_dir(d)


def test_checkpoint_roundtrip():
    project_id = str(uuid4())
    state = {
        "project_id": project_id,
        "status": "running",
        "requirements": {"title": "Test", "purpose": "Test purpose"},
        "source_code": None,
        "revision": 1,
        "token_usage": [{"agent": "test", "total_tokens": 100}],
        "errors": [],
        "warnings": [],
    }

    path = storage_service.save_checkpoint(project_id, state, "Test checkpoint")
    assert path.exists()
    assert path.suffix == ".json"

    loaded = storage_service.load_checkpoint(path)
    assert loaded["project_id"] == project_id
    assert loaded["state"]["requirements"]["title"] == "Test"


def test_list_checkpoints():
    p1, p2 = str(uuid4()), str(uuid4())
    storage_service.save_checkpoint(p1, {"project_id": p1}, "First")
    storage_service.save_checkpoint(p2, {"project_id": p2}, "Second")

    all_cps = storage_service.list_checkpoints()
    assert len(all_cps) == 2

    filtered = storage_service.list_checkpoints(project_id=p1)
    assert len(filtered) == 1
    assert p1 in filtered[0].stem


def test_save_and_load_generated_code():
    project_id = str(uuid4())
    files = [
        {"path": "src/main.py", "content": "print('hello')", "language": "python"},
        {"path": "src/utils/helpers.py", "content": "def help(): pass", "language": "python"},
        {"path": "README.md", "content": "# Test Project", "language": "markdown"},
    ]

    rev_dir = storage_service.save_generated_code(project_id, files, revision=1)
    assert rev_dir.exists()
    assert (rev_dir / "src" / "main.py").exists()
    assert (rev_dir / "src" / "utils" / "helpers.py").exists()
    assert (rev_dir / "README.md").exists()
    assert (rev_dir / "src" / "main.py").read_text() == "print('hello')"

    loaded = storage_service.load_generated_code(project_id, revision=1)
    assert len(loaded) == 3
    assert any(f["path"] == "src/main.py" for f in loaded)


def test_save_and_load_manifest():
    project_id = str(uuid4())
    manifest = {
        "project_id": project_id,
        "status": "completed",
        "artifacts": {"requirements": True, "source_code": False},
    }

    path = storage_service.save_manifest(project_id, manifest)
    assert path.exists()

    loaded = storage_service.load_manifest(project_id)
    assert loaded is not None
    assert loaded["status"] == "completed"
    assert loaded["artifacts"]["requirements"] is True


def test_create_backup():
    project_id = str(uuid4())
    storage_service.save_checkpoint(project_id, {"project_id": project_id}, "Pre-backup")
    storage_service.save_manifest(project_id, {"project_id": project_id, "status": "test"})

    backup_path = storage_service.create_backup(name="test_backup")
    assert backup_path.exists()
    assert backup_path.suffix == ".zip"


def test_export_project_zip():
    project_id = str(uuid4())
    state = {
        "requirements": {"title": "Test", "purpose": "Test purpose"},
        "architecture": {"pattern": "layered"},
        "source_code": {
            "files": [
                {"path": "main.py", "content": "print('hello')", "language": "python"},
            ]
        },
    }

    zip_path = storage_service.export_project_zip(project_id, state)
    assert zip_path.exists()
    assert zip_path.suffix == ".zip"


def test_clean_old_checkpoints():
    project_id = str(uuid4())
    for i in range(15):
        storage_service.save_checkpoint(project_id, {"project_id": project_id, "rev": i}, f"Checkpoint {i}")

    removed = storage_service.clean_old_checkpoints(keep_last=5)
    assert removed == 10

    remaining = storage_service.list_checkpoints(project_id)
    assert len(remaining) == 5
