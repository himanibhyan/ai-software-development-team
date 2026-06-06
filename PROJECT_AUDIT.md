# PROJECT AUDIT: AI Software Development Team

**Audit Date:** 2026-06-06
**Repository Root:** `/Users/himani/ai-software-development-team`
**Python Version:** 3.13.9 (`.venv` at `backend/.venv/`)

---

## 1. Existing Architecture

### 1.1 Overview

Clean layered architecture with clear separation of concerns:

```
├── backend/app/
│   ├── agents/          # 6 AI agents + base class + registry + prompts
│   ├── api/             # FastAPI router, deps, v1 endpoints
│   ├── core/            # Exceptions, security, logging, middleware
│   ├── db/              # Base, session, repositories (base/project/artifact)
│   ├── graph/           # LangGraph pipeline (state, nodes, edges, validation)
│   ├── models/          # Domain models, DB models (SQLAlchemy), API schemas
│   ├── services/        # Storage, Persist, LLM, VectorStore services
│   ├── worker/          # Celery app, tasks, event publisher
│   ├── config.py        # Pydantic Settings
│   ├── server.py        # FastAPI app factory
│   └── main.py          # Entry point
├── checkpoints/         # Pipeline state checkpoints (root level)
├── backups/             # Versioned file backups (root level)
├── storage/             # generated_code/, manifests/, logs/, exports/
├── docker/              # EMPTY
├── docs/                # SRS, architecture, folder structure, roadmap
├── infra/scripts/       # init-db.sql
├── scripts/             # EMPTY
├── src/                 # Stub/placeholder directories
│   ├── agents/
│   ├── api/
│   ├── database/
│   ├── frontend/
│   └── langgraph/
├── recover_project.py   # Disaster recovery script
├── project_manifest.json
├── Makefile
├── docker-compose.yml   # postgres, redis, chromadb, api, worker
├── docker-compose.dev.yml
```

### 1.2 Technology Stack

| Component | Technology | Status |
|-----------|-----------|--------|
| API Framework | FastAPI 0.111.0 | ✅ |
| Orchestration | LangGraph 0.1.2 | ✅ |
| LLM | OpenAI (AsyncOpenAI) | ✅ |
| Database ORM | SQLAlchemy 2.0.31 (async) | ✅ |
| Database | PostgreSQL 16 (asyncpg) | ✅ configured, not running |
| Vector Store | ChromaDB 0.5.0 | ✅ configured, not running |
| Task Queue | Celery 5.4+ | ✅ configured, not running |
| Message Broker | Redis 7 | ✅ configured, not running |
| Auth | python-jose, passlib+bcrypt | ✅ (bcrypt known issue) |
| Logging | structlog | ✅ |
| Testing | pytest, pytest-asyncio, httpx | ✅ |
| Containerization | Docker Compose | ✅ configured |

### 1.3 Dependency Conflicts

| Issue | Details |
|-------|---------|
| `passlib` + `bcrypt==5.0.0` on Python 3.13 | Incompatible — 4 tests xfailed |
| `langchain==1.2.15` + `langchain-core` | `langchain.debug` attribute missing; workaround in conftest.py |
| Root `requirements.txt` vs `backend/requirements/` | Duplicate dependency declarations, potential drift |

---

## 2. Existing Agents

### 2.1 BaseAgent (backend/app/agents/base.py — 174 lines)

- Abstract class with `process()` method, retry logic (2 retries), LLM integration
- `_validate_output()` / `_build_state_updates()` template methods
- `STATE_FIELD_MAP` maps agent type → state key
- Coverage: 100%

### 2.2 Requirements Agent (304 lines)

| Aspect | Assessment |
|--------|-----------|
| Prompt | Full SRS prompt with few-shot example, anti-patterns, quality rules (266 lines) |
| Validation | Min counts, ID format (FR-XX), priority distribution, vague term detection, category coverage, user story format |
| Sanitization | Whitespace, priority normalization, dedup, ID padding |
| Coverage | 21 tests |

### 2.3 Architect Agent (441 lines)

| Aspect | Assessment |
|--------|-----------|
| Prompt | Full architecture prompt with design principles, quality rules, anti-patterns (215 lines) |
| Validation | Component DAG check, tech stack quality, DB design (PK, columns), API spec, folder structure, Mermaid diagram, deployment strategy |
| Sanitization | Recursive folder entry cleaning, normalization of all nested models |
| Coverage | 21 tests |

### 2.4 Developer Agent (64 lines)

| Aspect | Assessment |
|--------|-----------|
| Prompt | 33 lines — basic instructions, no few-shot example |
| Validation | Only checks "has files" and "has main entry point" |
| Sanitization | **NONE** — inherits empty `_sanitize_output` from BaseAgent |
| Review Feedback | Reads `review_report` for rework context |
| Coverage | Covered via test_nodes.py (no dedicated test file) |
| **Risk** | **Thinnest agent** — no deep validation, no sanitization, no quality checks on generated code |

### 2.5 Tester Agent (55 lines)

| Aspect | Assessment |
|--------|-----------|
| Prompt | 29 lines — basic instructions, no few-shot example |
| Validation | Only checks "has at least one test case" |
| Sanitization | **NONE** |
| Coverage | No dedicated test file |
| **Risk** | No validation of test quality, no coverage targets enforced |

### 2.6 Code Review Agent (54 lines)

| Aspect | Assessment |
|--------|-----------|
| Prompt | 26 lines — basic review criteria, no few-shot example |
| Validation | Only checks score is 0-10 |
| Sanitization | **NONE** |
| Coverage | No dedicated test file |
| **Risk** | No validation of review content quality |

### 2.7 Documentation Agent (68 lines)

| Aspect | Assessment |
|--------|-----------|
| Prompt | 19 lines — basic instructions, no few-shot example |
| Validation | **NONE** — inherits empty `_validate_output` from BaseAgent |
| Sanitization | **NONE** |
| Coverage | No dedicated test file |
| **Risk** | **Least validated agent** — no quality enforcement at all |

### 2.8 Agent Registry (72 lines)

- Singleton pattern with lazy instantiation
- All 6 agents registered
- Coverage: adequate

---

## 3. Existing Tests

### 3.1 Test Summary

| Test Suite | Files | Tests | Status |
|-----------|-------|-------|--------|
| Unit tests | 17 files | ~260 | ✅ Passing |
| Integration tests | 2 files | 7 | ✅ Passing (pipeline) |
| Integration tests | 1 file | 9 | ❌ Failing (API — needs PostgreSQL) |
| E2E tests | 0 files | 0 | ❌ Missing |
| **Total** | **20 files** | **~276** | **260 pass, 4 xfailed, 9+ fail** |

### 3.2 Unit Test Files

| File | Tests | Coverage Target |
|------|-------|----------------|
| test_exceptions.py | 15 | `core/exceptions.py` 100% |
| test_llm_service.py | 14 | `services/llm_service.py` 100% |
| test_vector_store.py | 18 | `services/vector_store.py` 100% |
| test_nodes.py | 30 | `graph/nodes.py` 98% |
| test_base_repository.py | 15 | `db/repositories/base.py` 100% |
| test_state.py | 9 | `graph/state.py` ~95% |
| test_edges.py | 16 | `graph/edges.py` ~93% |
| test_validation.py | 12 | `graph/validation.py` ~70% |
| test_requirements_agent.py | 21 | `agents/requirements_agent.py` ~95% |
| test_architect_agent.py | 21 | `agents/architect_agent.py` ~95% |
| test_domain_models.py | — | `models/domain/project.py` 99% |
| test_artifact_models.py | — | `models/domain/artifact.py` 100% |
| test_enums.py | — | `models/domain/enums.py` 100% |
| test_registry.py | — | `agents/registry.py` ~90% |
| test_security.py | 10 | `core/security.py` 96% (4 xfailed) |
| test_storage_service.py | 7 | `services/storage_service.py` 72% |
| test_persist_service.py | — | `services/persist_service.py` 100% |
| test_graph_resume.py | — | `graph/pipeline.py` 100% |

### 3.3 Test Infrastructure Issues

| Issue | Impact |
|-------|--------|
| JSONB columns in SQLite test DB | API integration tests fail (9 tests) |
| No PostgreSQL in CI | Can't run API or repository integration tests |
| Mock data doesn't match Pydantic schemas | Pipeline integration tests use minimal mock data that may not reflect real validation |
| No E2E tests | Full pipeline from API → DB → disk never validated |
| No load/stress tests | No performance baseline |

---

## 4. Existing Persistence Layer

### 4.1 StorageService (408 lines — `app/services/storage_service.py`)

| Capability | Status | Notes |
|-----------|--------|-------|
| Checkpoint save/load | ✅ | JSON to `checkpoints/` directory |
| ZIP backup | ✅ | Timestamped, includes checkpoints + manifests |
| Generated code persistence | ✅ | `storage/generated_code/{project_id}/rev_{N}/` |
| Manifest management | ✅ | `storage/manifests/{project_id}.json` |
| Execution logs (NDJSON) | ✅ | `storage/logs/{project_id}.ndjson` |
| Project ZIP export | ✅ | All artifacts as JSON + generated files |
| Folder export | ✅ | Directory tree on disk |
| Snapshot export | ✅ | ZIP + folder + manifest |
| Versioned file backup | ✅ | `backups/filename_v{N}.ext` |
| Old checkpoint cleanup | ✅ | Configurable retention |
| Coverage | 72% | |

### 4.2 PersistService (129 lines — `app/services/persist_service.py`)

- Orchestrates DB + disk persistence
- `persist_agent_output()` — saves artifact to DB + disk checkpoint
- `finalize_project()` — updates status, creates backup + manifest
- Coverage: 100%

### 4.3 Disaster Recovery

- `recover_project.py` — standalone recovery from checkpoints
- **Issue**: Uses `generated/` path for output, but StorageService uses `storage/generated_code/`
- **Issue**: Manifest paths point to project root but persistent manifests go to `storage/manifests/`
- No automated recovery test

### 4.4 DB Models (SQLAlchemy)

| Model | Table | Key Features |
|-------|-------|-------------|
| `ProjectModel` | `projects` | JSONB constraints, status enum, timestamps |
| `ArtifactModel` | `project_artifacts` | JSONB content, unique(project, agent_type, revision) |
| `ExecutionModel` | `agent_executions` | Token tracking, error JSONB |

**Issues:**
- `JSONB` columns are PostgreSQL-specific — no SQLite fallback
- Alembic `versions/` directory is empty — no migrations generated
- `init-db.sql` creates tables directly, bypassing Alembic

---

## 5. Existing LangGraph Workflow

### 5.1 Pipeline Structure

```
START → validate_input ──(failed)──▶ error_handler ──▶ END
              │
              ▼
       requirements_agent ──(failed)──▶ error_handler
              │
              ▼
       architect_agent ──(failed)──▶ error_handler
              │
              ▼
       developer_agent ──(failed)──▶ error_handler
              │
              ▼
       code_review_agent
         │           │
         │ (score<6) │ (score≥6 ∨ max_attempts)
         ▼           │
    developer_agent  │
         │           │
         └───────────┘
                      │
                      ▼
              tester_agent ──(failed)──▶ error_handler
                      │
                      ▼
              documentation_agent
                      │
                      ▼
              persistence_node ──▶ END
```

### 5.2 Nodes (9 total)

| Node | Function | Lines | Coverage |
|------|----------|-------|----------|
| `validate_input_node` | Input validation (min 10 chars) | 30 | 98% |
| `requirements_node` | Invokes Requirements agent | 20 | 98% |
| `architect_node` | Invokes Architect agent | 20 | 98% |
| `developer_node` | Invokes Developer agent (with rework support) | 32 | 98% |
| `code_review_node` | Invokes Code Review agent, increments attempts | 28 | 98% |
| `tester_node` | Invokes Tester agent | 18 | 98% |
| `documentation_node` | Invokes Documentation agent | 18 | 98% |
| `persistence_node` | Saves final state, code, manifest | 78 | 98% |
| `error_node` | Handles unrecoverable errors | 16 | 98% |

### 5.3 Edge Functions (8 routing functions)

| Function | Routes | Coverage |
|----------|--------|----------|
| `route_after_validation` | → requirements / error | 93% |
| `route_after_requirements` | → architect / error | 93% |
| `route_after_architecture` | → developer / error | 93% |
| `route_after_development` | → code_review / error | 93% |
| `route_after_code_review` | → tester / developer / error | 93% |
| `route_after_testing` | → documentation / error | 93% |
| `route_after_documentation` | → persistence (always) | 93% |
| `should_continue` | → end / continue | Not tested |

### 5.4 State (GraphState TypedDict)

- 19 fields including artifacts, metadata, tracking, resume support
- `operator.add` reducers on lists (errors, warnings, token_usage, agent_results, completed_steps, pending_steps)
- `create_initial_state()` — factory with defaults
- `state_summary()` — human-readable summary
- `resume_mode` — fast-forward through completed steps
- Coverage: ~95%

### 5.5 Resume/Checkpoint Support

| Feature | Status |
|---------|--------|
| Per-step checkpoint save | ✅ In every node |
| Resume from checkpoint | ✅ `resume_from_checkpoint()` |
| Fast-forward completed steps | ✅ `_should_skip()` logic |
| Execution logs | ✅ NDJSON per project |
| MemorySaver (LangGraph) | ✅ In-memory checkpointing |

### 5.6 Pipeline Issues

| Issue | Details |
|-------|---------|
| Sync `pipeline.invoke()` in worker/tasks.py | All nodes are `async def` — `.invoke()` may not work correctly with async nodes. Should use `ainvoke()` or ensure nodes are sync-compatible |
| No pipeline timeout | Long-running agents could hang indefinitely |
| No circuit breaker | No mechanism to stop runaway rework loops beyond max_attempts |
| Error handling swallows exceptions in persistence_node | Storage failure is logged but never propagated |

---

## 6. What Is Complete

| Component | Status |
|-----------|--------|
| All 6 agents implemented (Requirements, Architect, Developer, Tester, Code Review, Documentation) | ✅ |
| LangGraph pipeline with 9 nodes, 8 edge routers | ✅ |
| Pipeline resume from checkpoint | ✅ |
| Code review rework loop (score < 6.0 → rework) | ✅ |
| Disk-based checkpoint/backup/export | ✅ |
| DB persistence layer (repositories, models) | ✅ |
| FastAPI application factory with lifespan | ✅ |
| 5 REST API endpoints (create, list, get, refine, delete, status) | ✅ |
| Celery worker task for async pipeline execution | ✅ |
| Docker Compose for all services (postgres, redis, chromadb, api, worker) | ✅ |
| Alembic migration setup | ✅ |
| Disaster recovery script | ✅ |
| Configuration via Pydantic Settings + .env | ✅ |
| Structured logging (structlog) | ✅ |
| CORS, request logging, process time middleware | ✅ |
| API key authentication dependency | ✅ |
| JWT token creation/verification | ✅ |
| Password hashing (bcrypt) | ✅ |
| ChromaDB vector store service | ✅ |
| OpenAI LLM service with retry logic | ✅ |
| 260 passing unit tests, 78% coverage | ✅ |
| All Pydantic domain models with validation | ✅ |
| Requirements agent complete with deep validation | ✅ |
| Architect agent complete with deep validation | ✅ |
| Test infrastructure with SQLite fixtures | ✅ |
| `.env.example`, `.gitignore`, `Makefile` | ✅ |

---

## 7. What Is Partially Complete

| Component | Status | Missing |
|-----------|--------|---------|
| Developer Agent | ~60% | No deep validation, no sanitization, no quality checks, no few-shot prompt |
| Tester Agent | ~50% | No validation beyond "has test cases", no coverage enforcement, no few-shot prompt |
| Code Review Agent | ~50% | No validation beyond score range, no few-shot prompt |
| Documentation Agent | ~40% | **No validation at all**, no sanitization, no few-shot prompt |
| Coverage | 78% | Target is 80%+; 8 files below 70% |
| API Integration Tests | ~30% | 9 tests written but all fail without PostgreSQL |
| Worker Tasks | ~60% | Sync invoke may be wrong for async nodes; registry init pattern is fragile |
| Recovery Script | ~70% | Path mismatches with StorageService |
| DB Migrations | ~10% | Alembic configured but no migrations created |
| Docker configuration | ~80% | `docker/` directory is empty |

---

## 8. What Is Missing

### 8.1 Missing Tests
- No E2E tests (empty `tests/e2e/` directory)
- No load/stress tests
- No performance benchmarks
- No security/penetration tests
- No tests for Developer, Tester, Code Review, or Documentation agents
- No tests for `app/worker/tasks.py`, `app/worker/celery_app.py`, `app/worker/events.py`
- No tests for `app/api/v1/projects.py`, `app/api/router.py`, `app/api/deps.py`
- No tests for `app/core/middleware.py`
- No tests for `app/db/session.py`
- No tests for `app/models/schemas/` (requests, responses)
- No tests for recovery/disaster scenarios

### 8.2 Missing Functionality
- **Frontend** — Mentioned in docs/README but not present
- **WebSocket support** — `websockets` in requirements but no WebSocket endpoint
- **Event streaming** — `EventPublisher` has TODO for Redis pub/sub, not wired to anything
- **GitHub export** — `ExportProjectRequest` schema exists but no implementation
- **Rate limiting** — `RateLimitException` exists, `RATE_LIMIT_*` settings exist, but no rate limiting middleware
- **Authentication middleware** — JWT/API key dependencies exist but no auth middleware protecting routes
- **Prometheus/Grafana** — Mentioned in docs but not configured
- **CI/CD pipeline** — No GitHub Actions or CI config
- **Frontend monitoring** — Sentry mentioned in prompts but not configured

### 8.3 Missing Infrastructure
- No `docker/` directory content
- No `scripts/` directory content  
- No migration files in `alembic/versions/`
- No production config (gunicorn, nginx, etc.)
- No health check endpoint testing
- No pre-commit hooks

---

## 9. Technical Debt

### 9.1 Code Quality Issues

| Issue | Location | Severity |
|-------|----------|----------|
| Sync `pipeline.invoke()` with all async nodes | `backend/app/worker/tasks.py:68` | **HIGH** — may cause runtime errors |
| Recovery script path mismatch | `recover_project.py:100` uses `generated/` instead of `storage/generated_code/` | **HIGH** — recovery will not find files |
| Manifest path mismatch | `recover_project.py:77` writes to project root, not `storage/manifests/` | **MEDIUM** |
| Thinnest 4 agents lack validation/sanitization | `developer_agent.py`, `tester_agent.py`, `code_review_agent.py`, `documentation_agent.py` | **MEDIUM** |
| No DB migrations created | `backend/alembic/versions/` is empty | **MEDIUM** |
| Dependency duplication | Root `requirements.txt` vs `backend/requirements/*.txt` | **MEDIUM** |
| Empty scaffolding directories | `docker/`, `scripts/`, `src/` | **LOW** |
| Configuration key mismatch | `.env.example` uses `CHROMADB_HOST` but `config.py` uses `CHROMA_HOST` | **LOW** |
| `init-db.sql` bypasses Alembic | Creates tables directly instead of using migrations | **LOW** |
| Mock data doesn't match schemas | `test_pipeline.py` fixture data may not pass validation | **LOW** |

### 9.2 Test Debt

| Issue | Impact |
|-------|--------|
| SQLite `JSONB` incompatibility | 9 API tests can't run without PostgreSQL |
| No Per-Platform CI config | Can't run full test suite in CI |
| No E2E tests | No confidence in end-to-end flow |
| 4 xfailed tests (bcrypt) | Security module not fully tested on Python 3.13 |
| `EventPublisher` untested | No tests for streaming/events |

### 9.3 Known Library Incompatibilities

| Library | Issue | Workaround |
|---------|-------|------------|
| `passlib[bcrypt]` + `bcrypt==5.0.0` on Python 3.13 | `passlib` not compatible with `bcrypt>=4.1` | Pin bcrypt<4.1 or use `bcrypt` directly |
| `langchain==1.2.15` + `langchain-core` | Missing `langchain.debug` attribute | `langchain.debug = False` in conftest.py |

---

## 10. Coverage Gaps

### 10.1 Files Below 80% Coverage

| File | Coverage | Reason |
|------|----------|--------|
| `app/server.py` | 56% | Needs HTTP server to test lifespan, middleware, exception handlers |
| `app/db/repositories/artifact_repo.py` | 59% | Needs PostgreSQL |
| `app/db/repositories/project_repo.py` | 60% | Needs PostgreSQL |
| `app/core/middleware.py` | 58% | Needs HTTP server |
| `app/graph/validation.py` | 70% | Needs richer test data for architect branch coverage |
| `app/db/session.py` | 47% | Needs PostgreSQL |
| `app/worker/tasks.py` | 43% | Needs Celery/Redis |
| `app/services/storage_service.py` | 72% | Can reach 80%+ with more edge cases |
| `app/api/v1/projects.py` | 39% | Needs PostgreSQL + HTTP server |

### 10.2 Untested Files

| File | Coverage | Notes |
|------|----------|-------|
| `app/worker/celery_app.py` | 0% | No Celery available |
| `app/worker/events.py` | 0% | No test file |
| `app/api/router.py` | 0% | Trivial, covered by API tests |
| `app/api/deps.py` | 0% | No auth tests |
| `app/main.py` | 0% | Entry point, hard to test |
| `app/models/schemas/requests.py` | 0% | No schema tests |
| `app/models/schemas/responses.py` | 0% | No schema tests |
| `app/models/db/*.py` | 0% | SQLAlchemy models, need DB |
| `app/db/base.py` | 0% | Base/Timestamp/UUID mixins |

---

## 11. Deployment Gaps

| Gap | Details | Priority |
|-----|---------|----------|
| No CI/CD | No GitHub Actions, Jenkins, or other CI config | **HIGH** |
| No production Dockerfile | Dockerfile has dev/prod stages but prod target may need tuning | **MEDIUM** |
| Alembic migrations not created | `alembic upgrade head` will fail with "no migrations" | **HIGH** |
| No SSL/TLS termination | API serves HTTP directly, no nginx/reverse proxy | **MEDIUM** |
| No secrets management | API keys in env vars, no Vault/Secrets Manager integration | **MEDIUM** |
| No health check on API | `/health` endpoint exists but no container healthcheck configured | **LOW** |
| Worker doesn't scale | Single Celery worker, no concurrency tuning | **LOW** |
| No monitoring stack | Prometheus/Grafana mentioned in docs but not in docker-compose | **MEDIUM** |
| No backup/restore automation | `recover_project.py` exists but not integrated with ops | **LOW** |
| No rate limiting in production | `RATE_LIMIT_*` settings exist but no middleware | **MEDIUM** |
| Frontend not deployed | React/Next.js frontend mentioned but doesn't exist | **MEDIUM** (blocker for full product) |

---

## 12. Recommendations by Priority

### P0 — Must Fix
1. Fix sync `pipeline.invoke()` → `ainvoke()` in `worker/tasks.py`
2. Create initial Alembic migration
3. Fix `recover_project.py` path mismatches
4. Set up CI/CD (GitHub Actions) with PostgreSQL service container

### P1 — Should Fix
5. Add validation/sanitization to Developer, Tester, Code Review, Documentation agents
6. Add dedicated test files for Developer, Tester, Code Review, Documentation agents
7. Reach 80% total coverage (focus on `validation.py`, `storage_service.py`)
8. Resolve `passlib`+`bcrypt` incompatibility (pin bcrypt or switch to `hashing`)
9. Consolidate `requirements.txt` duplication

### P2 — Nice to Have
10. Add E2E tests for full pipeline
11. Implement rate limiting middleware
12. Wire EventPublisher to Redis pub/sub
13. Add auth middleware to protect API routes
14. Create WebSocket endpoint for real-time streaming
15. Add Prometheus + Grafana to docker-compose
16. Create the frontend application
17. Add load/stress tests
18. Clean up empty `docker/`, `scripts/`, `src/` directories
19. Fix `CHROMADB_HOST` vs `CHROMA_HOST` config key mismatch in `.env.example`

---

## Appendix A: File Inventory

### Backend Source (63 files)
- `backend/app/agents/` — 11 files (6 agents + base + registry + prompts + init)
- `backend/app/api/` — 5 files (router, deps, v1/projects, init x2)
- `backend/app/core/` — 6 files (exceptions, security, logging, middleware, init x2)
- `backend/app/db/` — 5 files (base, session, repositories/base/project/artifact, init)
- `backend/app/graph/` — 7 files (state, nodes, edges, pipeline, validation, init x2)
- `backend/app/models/` — 10 files (domain/{project,artifact,enums}, db/{project,artifact,execution}, schemas/{requests,responses}, inits)
- `backend/app/services/` — 6 files (storage, persist, llm, vector_store, init x2)
- `backend/app/worker/` — 5 files (celery_app, tasks, events, init x2)
- `backend/app/config.py`, `server.py`, `main.py`, `__init__.py`

### Backend Tests (20 files)
- `backend/tests/conftest.py`
- `backend/tests/unit/` — 17 test files
- `backend/tests/integration/` — 2 files (conftest + test_pipeline)
- `backend/tests/fixtures/` — 2 fixtures (sample_idea.txt, mock_agent_responses.json)
- `backend/tests/e2e/` — empty

### Root Infrastructure (19 files)
- `project_manifest.json`, `recover_project.py`, `.gitignore`, `.env.example`, `requirements.txt`, `Makefile`
- `docker-compose.yml`, `docker-compose.dev.yml`
- `docker/` (empty), `docs/` (8 files), `infra/scripts/init-db.sql`, `scripts/` (empty), `src/` (5 stub dirs)
- `checkpoints/`, `backups/`, `storage/` (6 subdirs)

### Backend Config
- `backend/pyproject.toml`, `backend/alembic.ini`, `backend/alembic/env.py`, `backend/Dockerfile`
- `backend/requirements/base.txt`, `dev.txt`, `prod.txt`
