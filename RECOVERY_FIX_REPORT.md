# Recovery System Fix Report

## Summary

Fixed two path mismatches in `recover_project.py` where the recovery script was writing to different locations than `StorageService` expects, and one path mismatch where recovery was writing to a different location than the application expects.

## Changes Made

### 1. Generated code output path

**Before:** `generated/{project_id}/rev_{N}/`

**After:** `storage/generated_code/{project_id}/rev_{N}/`

**Source of truth:** `StorageService` in `backend/app/services/storage_service.py` constructs this path as `{PROJECT_ROOT}/storage/generated_code/{project_id}/rev_{N}/`.

**Files affected:**
- `recover_project.py` — updated `GENERATED_CODE_DIR` constant and `restore_from_checkpoint()` output path

### 2. Manifest output path

**Before:** `project_manifest.json` (project root)

**After:** `storage/manifests/{project_id}.json`

**Source of truth:** `StorageService` writes manifests to `storage/manifests/`.

**Files affected:**
- `recover_project.py` — added `MANIFESTS_DIR` constant, updated manifest write logic to use `storage/manifests/{project_id}.json`

### 3. Recovery inspection artifacts

**New path:** `storage/recovered/{project_id}/` — a dedicated location for artifact JSONs (requirements, architecture, etc.) produced during recovery, keeping them separate from live data.

**Files affected:**
- `recover_project.py` — added `RECOVERED_DIR` constant, writes restored artifacts to `storage/recovered/`

### 4. New features

- Added `--dry-run` flag to `recover_project.py` to preview recovery without writing files
- Added `--list` flag to list available checkpoints

## Files Created

- `backend/tests/unit/test_recovery.py` — 19 tests covering checkpoint discovery, loading, path correctness (both old-and-new and new-and-legacy verification), content correctness, dry-run mode, and backup creation

## Verification

- All 19 recovery tests pass
- Ruff lint is clean on both `recover_project.py` and `test_recovery.py`
- No regressions in existing test suite

## Relevant Path Layout (After Fix)

```
{PROJECT_ROOT}/
├── checkpoints/                          # Checkpoint files (uncompressed JSON snapshots)
├── backups/                              # Full-project backup ZIP archives
├── storage/
│   ├── generated_code/{project_id}/rev_{N}/   # Generated source code files
│   ├── manifests/{project_id}.json             # Project manifests
│   ├── recovered/{project_id}/                 # Inspection artifacts from recovery
│   ├── logs/{project_id}.ndjson                # Execution logs (StorageService)
│   └── exports/                                # Export destination (StorageService)
├── recover_project.py                    # Fixed recovery script
└── backend/
    └── app/services/storage_service.py   # Canonical path definitions
```
