# Folder Structure
## AI Software Development Team v1.0

```
ai-software-development-team/
│
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docker-compose.dev.yml
├── Makefile
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── dev.txt
│   │   └── prod.txt
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                          # FastAPI application entrypoint
│   │   ├── config.py                        # Settings via pydantic-settings
│   │   ├── server.py                        # Application factory, lifespan
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py                    # Main API router
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── projects.py              # Project CRUD endpoints
│   │   │   │   ├── agents.py                # Agent control endpoints
│   │   │   │   ├── feedback.py              # Feedback endpoints
│   │   │   │   ├── export.py                # GitHub export endpoints
│   │   │   │   └── streaming.py             # SSE / WebSocket handlers
│   │   │   └── deps.py                      # Dependency injection (DB, Auth)
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py                  # JWT, API key auth
│   │   │   ├── rate_limiter.py              # Token bucket rate limiter
│   │   │   ├── exceptions.py                # Custom exception classes
│   │   │   └── middleware.py                # Logging, CORS, error handling
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                      # BaseAgent abstract class
│   │   │   ├── registry.py                  # Agent registration & lookup
│   │   │   ├── requirements_agent.py        # Requirements Agent
│   │   │   ├── architect_agent.py           # Architect Agent
│   │   │   ├── developer_agent.py           # Developer Agent
│   │   │   ├── tester_agent.py              # Tester Agent
│   │   │   ├── code_review_agent.py         # Code Review Agent
│   │   │   ├── documentation_agent.py       # Documentation Agent
│   │   │   └── prompts/
│   │   │       ├── __init__.py
│   │   │       ├── requirements.py          # System prompts
│   │   │       ├── architect.py
│   │   │       ├── developer.py
│   │   │       ├── tester.py
│   │   │       ├── code_review.py
│   │   │       └── documentation.py
│   │   │
│   │   ├── graph/
│   │   │   ├── __init__.py
│   │   │   ├── state.py                     # GraphState TypedDict / Pydantic
│   │   │   ├── pipeline.py                  # StateGraph construction
│   │   │   ├── nodes.py                     # Node function definitions
│   │   │   ├── edges.py                     # Conditional edge logic
│   │   │   └── validation.py                # State transition validators
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── domain/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── project.py               # Project domain model
│   │   │   │   ├── artifact.py              # Artifact domain model
│   │   │   │   └── enums.py                 # Status, AgentType enums
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── requests.py              # API request schemas
│   │   │   │   ├── responses.py             # API response schemas
│   │   │   │   └── events.py                # WebSocket event schemas
│   │   │   └── db/
│   │   │       ├── __init__.py
│   │   │       ├── project.py               # SQLAlchemy project model
│   │   │       ├── artifact.py               # SQLAlchemy artifact model
│   │   │       └── execution.py             # SQLAlchemy execution log model
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py              # Generation orchestrator
│   │   │   ├── llm_service.py               # OpenAI API wrapper
│   │   │   ├── vector_store.py              # ChromaDB service
│   │   │   ├── code_executor.py             # Sandboxed code execution
│   │   │   ├── github_sync.py               # GitHub API integration
│   │   │   └── file_generator.py            # Write artifacts to disk
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py                   # SQLAlchemy async session
│   │   │   ├── base.py                      # Declarative base
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       ├── project_repo.py           # Project CRUD operations
│   │   │       ├── artifact_repo.py          # Artifact CRUD operations
│   │   │       └── execution_repo.py         # Execution log operations
│   │   │
│   │   └── worker/
│   │       ├── __init__.py
│   │       ├── celery_app.py                 # Celery configuration
│   │       ├── tasks.py                      # Async task definitions
│   │       └── events.py                     # Event publishing
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                       # Fixtures, test DB setup
│       ├── unit/
│       │   ├── test_requirements_agent.py
│       │   ├── test_architect_agent.py
│       │   ├── test_developer_agent.py
│       │   ├── test_tester_agent.py
│       │   ├── test_code_review_agent.py
│       │   ├── test_documentation_agent.py
│       │   ├── test_orchestrator.py
│       │   └── test_state.py
│       ├── integration/
│       │   ├── test_pipeline.py
│       │   ├── test_chromadb.py
│       │   └── test_github_export.py
│       ├── e2e/
│       │   └── test_full_generation.py
│       └── fixtures/
│           ├── sample_idea.txt
│           └── expected_outputs/
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   │
│   ├── public/
│   │   ├── favicon.ico
│   │   └── assets/
│   │
│   └── src/
│       ├── app/
│       │   ├── layout.tsx                   # Root layout with providers
│       │   ├── page.tsx                     # Landing / new project page
│       │   ├── projects/
│       │   │   ├── page.tsx                 # Project list
│       │   │   └── [id]/
│       │   │       ├── page.tsx             # Project detail view
│       │   │       ├── artifacts.tsx        # Artifact viewer
│       │   │       └── streaming.tsx        # Live streaming view
│       │   └── api/
│       │       └── projects/
│       │           └── route.ts             # Next.js API route (optional proxy)
│       │
│       ├── components/
│       │   ├── ui/                          # Atomic UI components
│       │   │   ├── Button.tsx
│       │   │   ├── Input.tsx
│       │   │   ├── Card.tsx
│       │   │   ├── Modal.tsx
│       │   │   ├── Spinner.tsx
│       │   │   └── Badge.tsx
│       │   ├── layout/
│       │   │   ├── Header.tsx
│       │   │   ├── Sidebar.tsx
│       │   │   └── Footer.tsx
│       │   ├── project/
│       │   │   ├── IdeaForm.tsx             # New project submission form
│       │   │   ├── ProjectCard.tsx           # Project summary card
│       │   │   ├── ProjectStatus.tsx         # Status badge with progress
│       │   │   └── ArtifactViewer.tsx        # Tabbed artifact display
│       │   ├── agent/
│       │   │   ├── AgentTimeline.tsx         # Timeline of agent executions
│       │   │   ├── AgentNode.tsx            # Individual agent node in graph
│       │   │   └── AgentLog.tsx             # Agent execution log viewer
│       │   ├── code/
│       │   │   ├── CodeEditor.tsx           # Syntax-highlighted code viewer
│       │   │   ├── FileTree.tsx             # Project file navigation
│       │   │   └── DiffViewer.tsx           # Code diff display
│       │   └── feedback/
│       │       ├── FeedbackForm.tsx          # User feedback submission
│       │       └── ReviewComments.tsx        # Code review comments display
│       │
│       ├── hooks/
│       │   ├── useProject.ts                # Project API hooks
│       │   ├── useWebSocket.ts              # WebSocket connection hook
│       │   └── useStreaming.ts             # SSE streaming hook
│       │
│       ├── lib/
│       │   ├── api.ts                       # Axios/fetch client
│       │   ├── ws.ts                        # WebSocket client
│       │   └── utils.ts                     # Shared utilities
│       │
│       ├── store/
│       │   ├── projectStore.ts              # Zustand state for projects
│       │   └── uiStore.ts                   # UI state (theme, sidebar)
│       │
│       └── types/
│           ├── project.ts                   # TypeScript interfaces
│           ├── agent.ts
│           └── api.ts
│
├── infra/
│   ├── nginx/
│   │   ├── nginx.conf
│   │   └── ssl/
│   ├── monitoring/
│   │   ├── prometheus.yml
│   │   ├── grafana-dashboards/
│   │   └── alertmanager.yml
│   └── scripts/
│       ├── init-db.sql                     # PostgreSQL initialization
│       ├── seed-data.sql                   # Sample data for development
│       └── backup.sh
│
├── docs/                                    # Project documentation
│   ├── SRS.md
│   ├── ARCHITECTURE.md
│   ├── FOLDER_STRUCTURE.md
│   ├── ROADMAP.md
│   ├── API_REFERENCE.md
│   └── CONTRIBUTING.md
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                          # CI pipeline
│   │   ├── cd.yml                          # CD pipeline
│   │   └── lint.yml                        # Lint checks
│   ├── CODEOWNERS
│   └── PULL_REQUEST_TEMPLATE.md
│
└── scripts/
    ├── generate_project.sh                 # Bootstrap script
    ├── migrate.sh                          # Alembic migration helper
    └── seed_vectors.py                     # ChromaDB seeding script
```
