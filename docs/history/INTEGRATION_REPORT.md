# Integration Report — Frontend ↔ Backend

## Summary

The Phase 1 frontend dashboard has been fully connected to the existing FastAPI backend. This report documents every integration point, the data flow for each page, issues discovered during integration, and fixes applied.

## Backend Routes vs Frontend API Calls

| Method | Backend Route | Frontend Hook | Status |
|---|---|---|---|
| `POST` | `/api/v1/projects` | `useCreateProject` | ✅ Connected |
| `GET` | `/api/v1/projects` | `useProjects` | ✅ Connected |
| `GET` | `/api/v1/projects/{id}` | `useProjectDetail` | ✅ Connected |
| `GET` | `/api/v1/projects/{id}/status` | `useProjectStatus` | ✅ Connected |
| `POST` | `/api/v1/projects/{id}/refine` | — (not yet exposed in UI) | ⏸️ Phase 2 |
| `DELETE` | `/api/v1/projects/{id}` | — (not yet exposed in UI) | ⏸️ Phase 2 |
| `GET` | `/health` | — (internal) | ✅ |

## Integration Architecture

```
Browser ──→ http://localhost:5173 ──→ Vite Dev Server
                                        │
                                  proxy: /api → http://localhost:8000
                                        │
                                  FastAPI Backend
```

- In development, the Vite dev server proxies all `/api/*` requests to the FastAPI backend at `http://localhost:8000`. This avoids CORS entirely during development.
- The Axios instance (`src/lib/api.ts`) uses `baseURL: '/api/v1'`, so all API paths are relative (e.g., `api.get('/projects')` calls `/api/v1/projects`).
- A response interceptor normalizes errors: API `detail` is extracted from the response body; network failures produce a clear "No response from server" message.

## Data Flow by Page

### 1. Dashboard → Project Creation

```
User submits form
  → validate: idea.length >= 10, constraints JSON parseable
  → mutation.mutate({ idea, constraints })
  → Axios POST /api/v1/projects
  → Backend: 201 { project_id, status, status_url }
  → mutation.onSuccess:
      invalidateQueries('projects')
      navigate('/projects/{project_id}/monitor')
```

- `useCreateProject` uses `useMutation` from TanStack Query
- Form validation matches backend constraints (min_length=10)
- Error display uses the normalized error from the Axios interceptor
- On success, user is redirected to the Monitor page

**Verified:** ✅ All fields match the `CreateProjectRequest` schema exactly. The `status_url` response field is captured but not currently displayed.

### 2. Monitor Page → Status Polling

```
Component mounts with projectId from URL
  → useProjectStatus(projectId): GET /api/v1/projects/{id}/status
      → refetches every 1s while status is: running, pending, refining
      → stops when: completed, failed
  → useProjectDetail(projectId): GET /api/v1/projects/{id}
      → refetches every 2s while status is: running, pending, refining
      → stops when: completed, failed
```

- Two parallel queries: the lightweight status endpoint (1s interval) and the full detail endpoint (2s interval)
- Status endpoint returns: `project_id`, `status`, `idea`, `created_at`, `updated_at`, `completed_at`
- Detail endpoint returns full project with all artifacts
- Agent status cards use `AGENT_TO_FIELD` mapping to check which artifacts are populated

**Fixed:** `useProjectStatus` and `useProjectDetail` now include `refining` in their `shouldRefetch` check (was missing, causing polling to stop during refinement).

**Fixed:** Agent status detection now uses `AGENT_TO_FIELD` mapping (`architect` → `architecture`, `developer` → `source_code`, `code_review` → `review_report`, `tester` → `test_suite`) instead of incorrectly indexing `detail[agent]`.

**Verified:** ✅ Refetch conditions match all five project statuses. Polling stops correctly on completion or failure.

### 3. Results Viewer → Artifact Display

```
Component mounts with projectId from URL
  → useProjectDetail(projectId): GET /api/v1/projects/{id}
  → Maps response fields to tabs:
      requirements  → RequirementsView
      architecture  → ArchitectureView
      source_code   → SourceCodeView
      test_suite    → TestsView
      review_report → ReviewView
      documentation → DocumentationView
```

- Six tabs, each with a dedicated renderer component
- Tabs are disabled when the artifact field is `null`
- Each renderer safely accesses nested fields with optional chaining and fallbacks
- The backend returns each artifact as a raw dict (matching the domain model structure)
- The `review_report` field maps to artifact type `code_review` on the backend side

**Verified:** ✅ All six artifact fields in `ProjectDetailResponse` map to the correct frontend fields. The `review_report` ↔ `code_review` mapping in `get_project` is handled correctly — the frontend sees `review_report` as the JSON key.

### 4. Project History → Paginated List

```
Component mounts
  → useProjects({ page, pageSize, status }): GET /api/v1/projects
      → query params: page, page_size, status
  → Renders cards with status badges, dates, artifact counts
  → Status filter dropdown updates the query
  → Pagination controls update the page
```

- `useProjects` uses `placeholderData: (prev) => prev` to keep the previous page visible while loading the next
- Status filter sends `?status=completed` (not `?status_filter=completed`)

**Fixed:** The query parameter was incorrectly named `status_filter`. The FastAPI backend defines the parameter as `Query(None, alias="status")`, so the URL query key must be `status`. The frontend now sends `status` instead of `status_filter`.

**Verified:** ✅ Pagination and filtering match the backend's `page`, `page_size`, and `status` query parameters exactly.

## Issues Discovered and Fixed

| # | Issue | File | Fix |
|---|---|---|---|
| 1 | `useProjects` sent `status_filter` instead of `status` query param | `hooks/useProjects.ts` | Changed param key to `status` |
| 2 | `useProjectDetail` and `useProjectStatus` didn't poll during `refining` status | Both hooks | Added `refining` to `shouldRefetch` |
| 3 | No Axios response interceptor for normalized error handling | `lib/api.ts` | Added interceptor that extracts `detail` from error responses |
| 4 | Dashboard error display used nested optional chain on Axios error | `pages/DashboardPage.tsx` | Simplified to `mutation.error?.message` (works with interceptor) |
| 5 | Monitor agent status cards used wrong field names | `pages/MonitorPage.tsx` + `lib/types.ts` | Added `AGENT_TO_FIELD` mapping |
| 6 | Backend `list_projects` omits `artifact_count` (field defaults to 0) | `projects.py:82-90` | Backend issue — frontend handles via default `=0` |

## Type Compatibility

Every backend Pydantic model has an exact TypeScript counterpart:

| Backend | Frontend | Match |
|---|---|---|
| `CreateProjectRequest` | `CreateProjectRequest` | ✅ |
| `CreateProjectResponse` | `CreateProjectResponse` | ✅ |
| `ProjectSummaryResponse` | `ProjectSummaryResponse` | ✅ (artifact_count defaults to 0) |
| `ProjectDetailResponse` | `ProjectDetailResponse` | ✅ |
| `PaginatedResponse` | `PaginatedResponse<T>` | ✅ |
| `ProjectStatusResponse` | `ProjectStatusResponse` | ✅ (from `/status` dict) |
| `RefineProjectRequest` | `RefineProjectRequest` | ✅ (not yet used in UI) |
| `ProjectStatus` enum | `ProjectStatus` type | ✅ |

## Network Flow

All four pages use the same data flow pattern:

```
TanStack Query hook
  → manages cache, deduplication, refetchInterval
  → calls Axios method
    → interceptor normalizes errors
    → Axios sends request to Vite proxy
      → proxy forwards to FastAPI
        → FastAPI processes, returns JSON
```

- TanStack Query provides automatic retry (2 attempts), stale-while-revalidate (10s staleTime), and cache invalidation
- No loading states are missed: every query returns `isLoading`, `error`, and `data`

## Running the Integration

```bash
# Terminal 1: Start backend
cd backend && uvicorn app.server:app --reload --port 8000

# Terminal 2: Start frontend (proxy → localhost:8000)
cd frontend && npm run dev
```

Open `http://localhost:5173` in a browser. The frontend communicates with the backend entirely through the Vite proxy — no CORS issues in development.

For production, either:
1. Serve the built frontend (`frontend/dist/`) from the FastAPI app as static files, or
2. Update `CORS_ORIGINS` in `backend/app/config.py` to include the frontend's production URL.

## Unresolved Items (Phase 2)

- `POST /api/v1/projects/{id}/refine` — endpoint exists but not exposed in UI (requires feedback form + re-generation trigger)
- `DELETE /api/v1/projects/{id}` — endpoint exists but not exposed in UI (requires confirmation dialog)
- Real-time WebSocket events — `EventPublisher` is stubbed; when implemented, can replace polling
