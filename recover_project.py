#!/usr/bin/env python3
"""
recover_project.py - Recovery Script for AI Software Development Team

Reconstructs the latest project state from checkpoints.
Usage:
    python recover_project.py [--checkpoint CHECKPOINT_FILE] [--list]

If no checkpoint specified, recovers from the latest checkpoint.
"""

import json
import os
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent
CHECKPOINTS_DIR = PROJECT_ROOT / "checkpoints"
BACKUPS_DIR = PROJECT_ROOT / "backups"
MANIFEST_PATH = PROJECT_ROOT / "project_manifest.json"


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


def get_latest_checkpoint() -> Optional[Path]:
    """Get the latest checkpoint file by modification time."""
    checkpoints = sorted(CHECKPOINTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not checkpoints:
        return None
    return checkpoints[-1]


def load_checkpoint(checkpoint_path: Path) -> dict:
    """Load a checkpoint file."""
    with open(checkpoint_path, "r") as f:
        return json.load(f)


def restore_from_checkpoint(checkpoint: dict):
    """Restore project state from checkpoint data.

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
    print(f"Restoring from checkpoint: {checkpoint.get('project_id', 'unknown')}")
    print(f"Created: {checkpoint.get('timestamp', 'unknown')}")
    print(f"Description: {checkpoint.get('description', 'N/A')}")

    state = checkpoint.get("state", {})

    # Reconstruct the project_manifest.json from checkpoint state
    if state:
        manifest_path = PROJECT_ROOT / "project_manifest.json"
        manifest = {
            "project_name": "AI Software Development Team (Recovered)",
            "version": state.get("revision", "unknown"),
            "description": f"Recovered from checkpoint: {checkpoint.get('description', 'N/A')}",
            "recovered_at": datetime.now().isoformat(),
            "project_id": checkpoint.get("project_id", "unknown"),
            "checkpoint_timestamp": checkpoint.get("timestamp", "unknown"),
            "status": state.get("status", "unknown"),
            "artifacts": {
                k: v is not None
                for k, v in state.items()
                if k in ("requirements", "architecture", "source_code", "test_suite", "documentation", "review_report")
            },
        }
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"  Restored: project_manifest.json")

    # Restore generated source code files
    source_code = state.get("source_code")
    if source_code and isinstance(source_code, dict):
        files = source_code.get("files", [])
        for entry in files:
            file_path = PROJECT_ROOT / "generated" / entry.get("path", "unknown")
            content = entry.get("content", "")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            print(f"  Restored: generated/{entry.get('path', 'unknown')}")

    restored_count = 0
    for key in ("requirements", "architecture", "test_suite", "documentation"):
        artifact = state.get(key)
        if artifact:
            artifact_path = PROJECT_ROOT / "generated" / f"{key}.json"
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(json.dumps(artifact, indent=2, default=str))
            print(f"  Restored: generated/{key}.json")
            restored_count += 1

    print(f"\nRecovery complete.")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Checkpoint: {checkpoint.get('description', 'N/A')}")
    print(f"Status: {state.get('status', 'unknown')}")
    if state.get("errors"):
        print(f"Errors: {len(state['errors'])}")


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
    restore_from_checkpoint(checkpoint)

    # Create backup before recovery
    backup_path = create_backup()
    print(f"Pre-recovery backup saved: {backup_path}")


if __name__ == "__main__":
    main()
