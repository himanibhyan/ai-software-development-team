# Dev Deployment Debug Log

## Issues Found & Fixed

### 1. ChromaDB connection hang
- **File**: `backend/app/services/vector_store.py`
- **Issue**: `chromadb.HttpClient()` hung indefinitely when ChromaDB wasn't running
- **Fix**: Wrapped in `asyncio.wait_for()` with 3s timeout and `run_in_executor()`

### 2. SQLAlchemy mapper initialization failure
- **File**: `backend/app/server.py`, `backend/app/models/db/__init__.py`
- **Issue**: `ExecutionModel` was only imported under `TYPE_CHECKING` in `project.py`, so SQLAlchemy mapper couldn't resolve the `"ExecutionModel"` string relationship
- **Fix**: Added explicit imports in `app/models/db/__init__.py` and `server.py`

### 3. PostgreSQL Enum vs StrEnum mismatch
- **File**: `backend/app/models/db/project.py`
- **Issue**: SQLAlchemy sent enum member **names** (`"PENDING"`) but PostgreSQL enum expected **values** (`"pending"`)
- **Fix**: Changed column type from `Enum(ProjectStatus, ...)` to `String(50)` — `ProjectStatus` is a `StrEnum` which provides Python-side validation

### 4. Celery dispatch with Redis unavailable
- **File**: `backend/app/api/v1/projects.py`
- **Issue**: `run_generation_pipeline.delay()` would fail when Redis wasn't running
- **Fix**: Added `_dispatch_pipeline()` helper that checks `settings.DISABLE_CELERY` and wraps the Celery call in try/except

### 5. ChromaDB init in startup lifespan
- **File**: `backend/app/services/vector_store.py`
- **Issue**: Synchronous HTTP call blocked async startup
- **Fix**: Moved to thread pool executor with timeout

## Services Status

| Service | Status | Port | Notes |
|---------|--------|------|-------|
| Backend (FastAPI) | ✅ Running | 8000 | CORS enabled for localhost:5173 |
| Frontend (Vite) | ✅ Running | 5173 | Proxies /api to backend |
| PostgreSQL | ✅ Available | 5432 | DB: ai_dev_team |
| Redis | ❌ Not available | - | Celery disabled via DISABLE_CELERY=true |
| ChromaDB | ❌ Not available | - | Initialize skipped gracefully (3s timeout) |
