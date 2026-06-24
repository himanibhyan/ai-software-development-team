# Deployment Report — Docker Full Stack

## Architecture

```
                          ┌─────────────┐
                          │   Frontend   │
                          │  Nginx :80   │
                          └──────┬──────┘
                                 │
                           /api/* proxy
                                 │
                          ┌──────▼──────┐
                          │  FastAPI API │
                          │  uvicorn     │
                          │  :8000       │
                          └──┬───┬───┬──┘
                             │   │   │
                    ┌────────┘   │   └────────┐
                    ▼            ▼            ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │ Postgres │ │  Redis   │ │ ChromaDB │
             │  :5432   │ │  :6379   │ │  :8000   │
             └──────────┘ └──────────┘ └──────────┘
                    │            │
                    └────────────┘
                         │
                    ┌────▼────┐
                    │  Celery │
                    │  Worker │
                    └─────────┘
```

## Service Overview (6 containers)

| Service | Container Name | Image | Port(s) | Purpose |
|---|---|---|---|---|
| `postgres` | `ai-dev-postgres` | `postgres:16-alpine` | `5432` | Primary database |
| `redis` | `ai-dev-redis` | `redis:7-alpine` | `6379` | Celery broker + cache |
| `chromadb` | `ai-dev-chromadb` | `chromadb/chroma:0.5.0` | `8001` | Vector store (agent memory) |
| `api` | `ai-dev-api` | custom (`backend/Dockerfile`) | `8000` | FastAPI backend |
| `worker` | `ai-dev-worker` | custom (`backend/Dockerfile`) | — | Celery async task worker |
| `frontend` | `ai-dev-frontend` | custom (`frontend/Dockerfile`) | `80` | Nginx serving React SPA |

## Files Created/Modified

| File | Action | Purpose |
|---|---|---|
| `docker-compose.yml` | **Rewritten** | Full 6-service orchestration with health checks, named volumes, shared env |
| `docker-compose.dev.yml` | **Updated** | Dev overrides: hot-reload mounts, verbose logging |
| `frontend/Dockerfile` | **Created** | Multi-stage: Node 20 build → Nginx 1.27-alpine serve |
| `frontend/nginx.conf` | **Created** | SPA routing + `/api/` reverse proxy + gzip + security headers |
| `frontend/.dockerignore` | **Created** | Excludes `node_modules`, `dist`, `.env` |
| `backend/Dockerfile` | **Updated** | Fixed uvicorn entry point to `app.server:app`; added healthcheck |
| `backend/.dockerignore` | **Created** | Excludes `__pycache__`, `.env`, `tests` |
| `Makefile` | **Updated** | Added `docker-*` targets for all deployment commands |
| `.env.example` | **Updated** | Cleaned up with Docker-relevant defaults |

## Frontend Dockerfile (`frontend/Dockerfile`)

Two-stage build:

1. **Build stage** (`node:20-alpine`): Installs production npm deps, runs `tsc -b && vite build` → outputs to `dist/`
2. **Serve stage** (`nginx:1.27-alpine`): Copies built assets + custom nginx config, serves on port 80

Nginx handles:
- **SPA routing**: `try_files $uri $uri/ /index.html` — all non-file routes serve `index.html`
- **API proxy**: `/api/` → `http://api:8000/api/` with proper headers
- **Static caching**: JS/CSS assets get 1-year cache headers
- **Gzip**: enabled for text content types
- **Security**: `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`

## Backend Dockerfile (`backend/Dockerfile`)

Three-stage build:

1. **Base** (`python:3.12-slim`): System deps, Python config
2. **Development**: Dev requirements + `--reload` uvicorn
3. **Production**: Prod requirements only, non-root `app` user, healthcheck

Key changes from original:
- Entry point fixed: `app.server:app` (was `app.main:app` which is indirect)
- Healthcheck added: `curl --fail http://localhost:8000/health`
- Production stage uses non-root user

## Docker Compose Details

### Shared Configuration

Environment variables shared by `api` and `worker`:
```yaml
DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/ai_dev_team
REDIS_URL: redis://redis:6379/0
CHROMA_HOST: chromadb
CHROMA_PORT: 8000
ENVIRONMENT: production
LOG_LEVEL: info
LOG_FORMAT: json
```

### Health Check Dependencies

```
postgres (healthy) ──┐
redis (healthy) ─────┤── api ── frontend
chromadb (healthy) ──┘
                      └── worker
```

All three infrastructure services must pass health checks before `api` and `worker` start.

### Named Volumes

| Volume | Mount Point | Purpose |
|---|---|---|
| `postgres_data` | `/var/lib/postgresql/data` | Database persistence |
| `chroma_data` | `/chroma/chroma-data` | Vector store persistence |
| `generated_projects` | `/app/generated_projects` | Generated code output |
| `storage_data` | `/app/storage` | Checkpoints, manifests, logs |

## Startup Commands

### First-time deployment

```bash
# 1. Copy environment file and set your OpenAI key
cp .env.example .env
# Edit .env — set OPENAI_API_KEY=sk-your-key

# 2. Build all images
make docker-build

# 3. Start everything
make docker-up

# 4. Check status
make docker-ps
```

### Quick start (if images already built)

```bash
make docker-up
```

### View logs

```bash
make docker-logs          # All services
make docker-api-logs      # API only
make docker-worker-logs   # Worker only
make docker-frontend-logs # Frontend only
```

### Stop services

```bash
make docker-down                 # Stop containers
make docker-down-volumes         # Stop + delete all data volumes
```

### Rebuild after code changes

```bash
make docker-build && make docker-restart
```

### Development mode (with hot-reload)

```bash
# Start infrastructure in background
make docker-infra-up

# Run API and frontend locally with hot-reload
cd backend && uvicorn app.server:app --reload --port 8000
cd frontend && npm run dev
```

## Access Points

| Service | URL |
|---|---|
| Frontend (SPA) | `http://localhost` |
| FastAPI (direct) | `http://localhost:8000` |
| API Docs (Swagger) | `http://localhost:8000/docs` |
| API Docs (ReDoc) | `http://localhost:8000/redoc` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |
| ChromaDB | `localhost:8001` |

All frontend API requests go through Nginx at `http://localhost/api/...` which proxies to the backend. No CORS needed.

## Environment Variables

Required in `.env`:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key for LLM agents |

Optional overrides:

| Variable | Default | Description |
|---|---|---|
| `OPENAI_MODEL` | `gpt-4-turbo-preview` | LLM model |
| `API_KEY` | `dev-api-key` | Backend API key |
| `SECRET_KEY` | `change-me-in-production` | JWT secret |
| `LOG_LEVEL` | `info` | Logging level |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | CORS allowed origins |

## Verification Checklist

After `make docker-up`, run these checks:

```bash
# 1. All containers running
docker compose ps

# 2. Frontend serves SPA
curl -s http://localhost | grep -q "root" && echo "Frontend OK"

# 3. Backend health endpoint
curl -s http://localhost:8000/health | grep -q "healthy" && echo "API OK"

# 4. API proxy through Nginx
curl -s http://localhost/api/v1/projects | grep -q "items" && echo "Proxy OK"
```

## Notes

- The frontend is served on port **80** (HTTP). No HTTPS is configured — add a reverse proxy (e.g., Caddy, Traefik) for production TLS.
- ChromaDB listens on `8001` (mapped from internal `8000`) to avoid conflicting with the API.
- Celery worker uses Redis as both broker and result backend.
- The `generated_projects` and `storage_data` volumes persist generated code and checkpoints across container restarts.
- To reset all data: `make docker-down-volumes` then `make docker-up`.
