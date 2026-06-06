#!/usr/bin/env python3
"""
recover_project.py - Recovery Script for AI Software Development Team

Reconstructs the latest project state from checkpoints.
Writes recovered files to paths that match the StorageService layout.

Usage:
    python recover_project.py [--checkpoint CHECKPOINT_FILE] [--list] [--dry-run]

If no checkpoint specified, recovers from the latest checkpoint.
Use --dry-run to preview what would be restored without writing files.
"""

import json
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CHECKPOINTS_DIR = PROJECT_ROOT / "checkpoints"
BACKUPS_DIR = PROJECT_ROOT / "backups"
STORAGE_DIR = PROJECT_ROOT / "storage"
GENERATED_CODE_DIR = STORAGE_DIR / "generated_code"
MANIFESTS_DIR = STORAGE_DIR / "manifests"
RECOVERED_DIR = STORAGE_DIR / "recovered"


def list_checkpoints():
    """List all available checkpoints."""
    checkpoints = sorted(CHECKPOINTS_DIR.glob("*.json"))
    if not checkpoints:
        print("No checkpoints found.")
        return []
    print("Available checkpoints:")
    for cp in checkpoints:
        size = cp.stat().st_size
        mtime = datetime.fromtimestamp(cp.stat().st_mtime).isoformat()
        print(f"  {cp.name} ({size} bytes, modified: {mtime})")
    return checkpoints


def get_latest_checkpoint() -> Path | None:
    """Get the latest checkpoint file by modification time."""
    checkpoints = sorted(CHECKPOINTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not checkpoints:
        return None
    return checkpoints[-1]


def load_checkpoint(checkpoint_path: Path) -> dict:
    """Load a checkpoint file."""
    with open(checkpoint_path) as f:
        return json.load(f)


def restore_from_checkpoint(checkpoint: dict, dry_run: bool = False):
    """Restore project state from checkpoint data.

    Matches the StorageService path layout:

      * generated code  → storage/generated_code/{project_id}/rev_{N}/
      * manifest        → storage/manifests/{project_id}.json
      * recovered JSONs → storage/recovered/{project_id}/

    Works with the StorageService checkpoint format:
    {
        "project_id": str,
        "timestamp": str,
        "description": str,
        "state": { ... full GraphState ... },
        "token_usage": [...],
        "errors": [...],
        "warnings": [...]
    }
    """
    project_id = checkpoint.get("project_id", "unknown")
    state = checkpoint.get("state", {})
    revision = state.get("revision", 1)

    label = "[DRY-RUN] " if dry_run else ""
    print(f"{label}Restoring from checkpoint: {project_id}")
    print(f"{label}  Created: {checkpoint.get('timestamp', 'unknown')}")
    print(f"{label}  Description: {checkpoint.get('description', 'N/A')}")
    print(f"{label}  Revision: {revision}")

    # ── Manifest ──────────────────────────────────────────────
    # Write to storage/manifests/{project_id}.json to match StorageService
    if state:
        _artifact_keys = (
            "requirements", "architecture", "source_code",
            "test_suite", "documentation", "review_report",
        )
        manifest = {
            "project_name": "AI Software Development Team (Recovered)",
            "version": revision,
            "description": f"Recovered from checkpoint: {checkpoint.get('description', 'N/A')}",
            "recovered_at": datetime.now().isoformat(),
            "project_id": project_id,
            "checkpoint_timestamp": checkpoint.get("timestamp", "unknown"),
            "status": state.get("status", "unknown"),
            "artifacts": {
                k: v is not None
                for k, v in state.items()
                if k in _artifact_keys
            },
        }
        manifest_path = MANIFESTS_DIR / f"{project_id}.json"
        if not dry_run:
            MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"{label}  Manifest: {manifest_path}")

    # ── Generated source code ─────────────────────────────────
    # Write to storage/generated_code/{project_id}/rev_{N}/
    source_code = state.get("source_code")
    if source_code and isinstance(source_code, dict):
        files = source_code.get("files", [])
        if files:
            rev_dir = GENERATED_CODE_DIR / project_id / f"rev_{revision}"
            if not dry_run:
                GENERATED_CODE_DIR.mkdir(parents=True, exist_ok=True)
            for entry in files:
                file_rel = entry.get("path", "unknown")
                file_path = rev_dir / file_rel
                content = entry.get("content", "")
                if not dry_run:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content)
                rel = f"storage/generated_code/{project_id}/rev_{revision}/{file_rel}"
                print(f"{label}  Restored: {rel}")

    # ── Artifact JSONs (for inspection / debugging) ───────────
    # Write to storage/recovered/{project_id}/ for reference
    restored_count = 0
    for key in ("requirements", "architecture", "test_suite", "documentation"):
        artifact = state.get(key)
        if artifact:
            artifact_path = RECOVERED_DIR / project_id / f"{key}.json"
            if not dry_run:
                artifact_path.parent.mkdir(parents=True, exist_ok=True)
                artifact_path.write_text(json.dumps(artifact, indent=2, default=str))
            print(f"{label}  Restored: storage/recovered/{project_id}/{key}.json")
            restored_count += 1

    print(f"{label}")
    print(f"{label}Recovery complete.")
    print(f"{label}  Status: {state.get('status', 'unknown')}")
    if state.get("errors"):
        print(f"{label}  Errors: {len(state['errors'])}")
    if dry_run:
        print(f"{label}  (dry-run — no files written)")


def create_backup():
    """Create a backup of current project state."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}"
    backup_dir = BACKUPS_DIR / backup_name
    backup_dir.mkdir(parents=True, exist_ok=True)

    for item in PROJECT_ROOT.iterdir():
        if item.name in ("checkpoints", "backups", "__pycache__", ".git", "node_modules", ".venv"):
            continue
        if item.is_file():
            shutil.copy2(item, backup_dir / item.name)
        elif item.is_dir():
            shutil.copytree(item, backup_dir / item.name, dirs_exist_ok=True)

    # Create zip archive
    zip_path = BACKUPS_DIR / f"{backup_name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in backup_dir.rglob("*"):
            zf.write(file_path, file_path.relative_to(backup_dir))

    print(f"Backup created: {zip_path}")
    return zip_path


def main():
    dry_run = "--dry-run" in sys.argv

    if "--list" in sys.argv:
        list_checkpoints()
        return

    checkpoint_path = None
    if "--checkpoint" in sys.argv:
        idx = sys.argv.index("--checkpoint")
        if idx + 1 < len(sys.argv):
            checkpoint_path = Path(sys.argv[idx + 1])
            if not checkpoint_path.exists():
                print(f"Error: Checkpoint file not found: {checkpoint_path}")
                sys.exit(1)

    if checkpoint_path is None:
        checkpoint_path = get_latest_checkpoint()
        if checkpoint_path is None:
            print("Error: No checkpoints found. Cannot recover.")
            sys.exit(1)
        print(f"Using latest checkpoint: {checkpoint_path.name}")

    checkpoint = load_checkpoint(checkpoint_path)
    restore_from_checkpoint(checkpoint, dry_run=dry_run)

    if not dry_run:
        backup_path = create_backup()
        print(f"Pre-recovery backup saved: {backup_path}")


if __name__ == "__main__":
    main()
