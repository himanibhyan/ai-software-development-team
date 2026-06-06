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
    checkpoints = sorted(CHECKPOINTS_DIR.glob("checkpoint_*.json"))
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
    """Get the latest checkpoint file."""
    checkpoints = sorted(CHECKPOINTS_DIR.glob("checkpoint_*.json"))
    if not checkpoints:
        return None
    return checkpoints[-1]


def load_checkpoint(checkpoint_path: Path) -> dict:
    """Load a checkpoint file."""
    with open(checkpoint_path, "r") as f:
        return json.load(f)


def restore_from_checkpoint(checkpoint: dict):
    """Restore project state from checkpoint data."""
    print(f"Restoring from checkpoint: {checkpoint.get('name', 'unknown')}")
    print(f"Created: {checkpoint.get('timestamp', 'unknown')}")
    print(f"Description: {checkpoint.get('description', 'N/A')}")

    files = checkpoint.get("files", [])
    restored_count = 0

    for file_info in files:
        file_path = PROJECT_ROOT / file_info["path"]
        content = file_info.get("content")
        if content is None:
            print(f"  Skipping {file_info['path']}: no content in checkpoint")
            continue

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            f.write(content)

        restored_count += 1
        print(f"  Restored: {file_info['path']}")

    print(f"\nRestored {restored_count} files successfully.")
    print(f"Project root: {PROJECT_ROOT}")


def create_backup():
    """Create a backup of current project state."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}"
    backup_dir = BACKUPS_DIR / backup_name
    backup_dir.mkdir(parents=True, exist_ok=True)

    for item in PROJECT_ROOT.iterdir():
        if item.name in ("checkpoints", "backups", "__pycache__", ".git"):
            continue
        if item.is_file():
            shutil.copy2(item, backup_dir / item.name)
        elif item.is_dir():
            shutil.copytree(item, backup_dir / item.name)

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
