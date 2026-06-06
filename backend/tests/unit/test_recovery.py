"""Tests for recover_project.py."""

import json
import sys
from pathlib import Path

import pytest

# Add project root to path so recover_project.py can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from recover_project import (  # noqa: E402
    create_backup,
    get_latest_checkpoint,
    list_checkpoints,
    load_checkpoint,
    restore_from_checkpoint,
)

# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary project root and monkeypatch path constants."""
    import recover_project as rp

    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    (tmp_path / "backups").mkdir()
    (tmp_path / "storage" / "generated_code").mkdir(parents=True)
    (tmp_path / "storage" / "manifests").mkdir(parents=True)
    (tmp_path / "storage" / "recovered").mkdir(parents=True)

    monkeypatch.setattr(rp, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(rp, "CHECKPOINTS_DIR", tmp_path / "checkpoints")
    monkeypatch.setattr(rp, "BACKUPS_DIR", tmp_path / "backups")
    monkeypatch.setattr(rp, "STORAGE_DIR", tmp_path / "storage")
    monkeypatch.setattr(rp, "GENERATED_CODE_DIR", tmp_path / "storage" / "generated_code")
    monkeypatch.setattr(rp, "MANIFESTS_DIR", tmp_path / "storage" / "manifests")
    monkeypatch.setattr(rp, "RECOVERED_DIR", tmp_path / "storage" / "recovered")

    return tmp_path


@pytest.fixture
def sample_checkpoint_data() -> dict:
    return {
        "project_id": "test-proj-123",
        "timestamp": "2026-06-06T12:00:00+00:00",
        "description": "Test checkpoint",
        "state": {
            "project_id": "test-proj-123",
            "status": "completed",
            "revision": 3,
            "requirements": {"title": "Test Reqs", "frs": []},
            "architecture": {"pattern": "microservices"},
            "source_code": {
                "files": [
                    {"path": "src/main.py", "content": "print('hello')"},
                    {"path": "src/utils.py", "content": "def util(): pass"},
                ]
            },
            "test_suite": None,
            "documentation": None,
            "review_report": None,
            "errors": [],
            "warnings": [],
        },
        "token_usage": [],
        "errors": [],
        "warnings": [],
    }


@pytest.fixture
def checkpoint_file(project_root: Path, sample_checkpoint_data: dict) -> Path:
    path = project_root / "checkpoints" / "test-proj-123_20260606_120000.json"
    path.write_text(json.dumps(sample_checkpoint_data))
    return path


# ── Tests: checkpoint listing / loading ───────────────────────────────


class TestCheckpointDiscovery:
    @pytest.mark.usefixtures("project_root")
    def test_list_checkpoints_empty(self):
        assert list_checkpoints() == []

    def test_list_checkpoints_with_files(self, checkpoint_file: Path):
        result = list_checkpoints()
        assert len(result) == 1
        assert result[0] == checkpoint_file

    def test_list_checkpoints_returns_sorted(self, project_root: Path):
        (project_root / "checkpoints" / "a_early.json").write_text("{}")
        (project_root / "checkpoints" / "b_later.json").write_text("{}")
        result = list_checkpoints()
        assert len(result) == 2

    @pytest.mark.usefixtures("project_root")
    def test_get_latest_checkpoint_no_files(self):
        assert get_latest_checkpoint() is None

    def test_get_latest_checkpoint_returns_most_recent(
        self, project_root: Path
    ):
        early = project_root / "checkpoints" / "early.json"
        late = project_root / "checkpoints" / "late.json"
        early.write_text("{}")
        late.write_text("{}")
        late.touch()
        result = get_latest_checkpoint()
        assert result == late


class TestCheckpointLoading:
    def test_load_checkpoint_returns_dict(self, checkpoint_file: Path):
        data = load_checkpoint(checkpoint_file)
        assert data["project_id"] == "test-proj-123"

    def test_load_checkpoint_raises_on_missing(self, project_root: Path):
        with pytest.raises(FileNotFoundError):
            load_checkpoint(project_root / "checkpoints" / "nonexistent.json")

    def test_load_checkpoint_preserves_state(self, checkpoint_file: Path):
        data = load_checkpoint(checkpoint_file)
        assert data["state"]["revision"] == 3
        assert data["state"]["source_code"]["files"][0]["path"] == "src/main.py"


# ── Tests: path correctness ───────────────────────────────────────────


class TestRestorePaths:
    def test_manifest_written_to_storage_manifests(
        self, project_root: Path, sample_checkpoint_data: dict
    ):
        restore_from_checkpoint(sample_checkpoint_data)
        manifest_path = (
            project_root / "storage" / "manifests" / "test-proj-123.json"
        )
        assert manifest_path.exists(), f"Expected manifest at {manifest_path}"
        manifest = json.loads(manifest_path.read_text())
        assert manifest["project_id"] == "test-proj-123"

    def test_manifest_not_written_to_project_root(
        self, project_root: Path, sample_checkpoint_data: dict
    ):
        restore_from_checkpoint(sample_checkpoint_data)
        old_path = project_root / "project_manifest.json"
        assert not old_path.exists(), f"Should NOT write to {old_path}"

    def test_generated_code_written_to_storage_generated_code(
        self, project_root: Path, sample_checkpoint_data: dict
    ):
        restore_from_checkpoint(sample_checkpoint_data)
        gen_dir = (
            project_root / "storage" / "generated_code" / "test-proj-123" / "rev_3"
        )
        for file_rel in ("src/main.py", "src/utils.py"):
            expected = gen_dir / file_rel
            assert expected.exists(), f"Expected generated code at {expected}"
            assert expected.read_text() != ""

    def test_generated_code_not_written_to_legacy_generated(
        self, project_root: Path, sample_checkpoint_data: dict
    ):
        restore_from_checkpoint(sample_checkpoint_data)
        old_dir = project_root / "generated"
        assert not old_dir.exists(), f"Should NOT write to legacy {old_dir}"

    def test_recovered_jsons_written_to_storage_recovered(
        self, project_root: Path, sample_checkpoint_data: dict
    ):
        restore_from_checkpoint(sample_checkpoint_data)
        for key in ("requirements", "architecture"):
            expected = (
                project_root
                / "storage"
                / "recovered"
                / "test-proj-123"
                / f"{key}.json"
            )
            assert expected.exists(), f"Expected recovered artifact at {expected}"

    def test_dry_run_does_not_write_files(
        self, project_root: Path, sample_checkpoint_data: dict
    ):
        restore_from_checkpoint(sample_checkpoint_data, dry_run=True)
        manifest = project_root / "storage" / "manifests" / "test-proj-123.json"
        gen_dir = (
            project_root / "storage" / "generated_code" / "test-proj-123" / "rev_3"
        )
        source = gen_dir / "src" / "main.py"
        recovered = (
            project_root
            / "storage"
            / "recovered"
            / "test-proj-123"
            / "requirements.json"
        )
        assert not manifest.exists()
        assert not source.exists()
        assert not recovered.exists()


# ── Tests: content correctness ────────────────────────────────────────


class TestRestoreContent:
    def test_restored_source_code_has_correct_content(
        self, project_root: Path, sample_checkpoint_data: dict
    ):
        restore_from_checkpoint(sample_checkpoint_data)
        main_path = (
            project_root
            / "storage"
            / "generated_code"
            / "test-proj-123"
            / "rev_3"
            / "src"
            / "main.py"
        )
        assert main_path.read_text() == "print('hello')"

    def test_restored_manifest_contains_artifact_status(
        self, project_root: Path, sample_checkpoint_data: dict
    ):
        restore_from_checkpoint(sample_checkpoint_data)
        manifest = json.loads(
            (project_root / "storage" / "manifests" / "test-proj-123.json").read_text()
        )
        assert manifest["artifacts"]["requirements"] is True
        assert manifest["artifacts"]["architecture"] is True
        assert manifest["artifacts"]["test_suite"] is False
        assert manifest["artifacts"]["documentation"] is False

    def test_restored_manifest_includes_recovered_metadata(
        self, project_root: Path, sample_checkpoint_data: dict
    ):
        restore_from_checkpoint(sample_checkpoint_data)
        manifest = json.loads(
            (project_root / "storage" / "manifests" / "test-proj-123.json").read_text()
        )
        assert "recovered_at" in manifest
        assert manifest["checkpoint_timestamp"] == "2026-06-06T12:00:00+00:00"
        assert manifest["status"] == "completed"
        assert manifest["version"] == 3


# ── Tests: backup ─────────────────────────────────────────────────────


class TestBackup:
    @pytest.mark.usefixtures("project_root")
    def test_create_backup_creates_zip(self):
        backup_path = create_backup()
        assert backup_path.exists()
        assert backup_path.suffix == ".zip"
        assert "backup" in backup_path.name

    def test_create_backup_creates_directory(self, project_root: Path):
        backup_path = create_backup()
        backup_dir = project_root / "backups" / backup_path.stem
        assert backup_dir.exists()
