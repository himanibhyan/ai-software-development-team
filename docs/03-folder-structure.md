# Folder Structure

## AI Software Development Team

**Version:** 1.0  
**Date:** 2026-06-06  
**Author:** Senior AI Architect  

---

```
ai-software-development-team/
│
├── project_manifest.json              # Project file tracking registry
├── recover_project.py                 # Disaster recovery script
│
├── checkpoints/                       # Automated checkpoint snapshots
│   ├── checkpoint_1_requirements.json
│   ├── checkpoint_2_architecture.json
│   └── checkpoint_3_backend.zip
│
├── backups/                           # Versioned file backups
│   └── (auto-generated backups)
│
├── docs/                              # Project documentation
│   ├── 01-software-requirements-specification.md
│   ├── 02-architecture-design-document.md
│   ├── 03-folder-structure.md
│   └── 04-development-roadmap.md
│
├── src/                               # Source code
│   ├── api/                           # FastAPI backend
│   │   ├── __init__.py
│   │   ├── main.py                    # Application entry point
│   │   ├── config.py                  # Configuration (pydantic-settings)
│   │   ├── dependencies.py            # FastAPI dependency injection
│   │   ├── exceptions.py              # Global exception handlers
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── projects.py            # Project CRUD (POST/GET/DELETE)
│   │   │   ├── workflow.py            # Workflow control (start/pause/resume)
│   │   │   ├── artifacts.py           # Artifact retrieval & download
│   │   │   └── health.py              # Health check endpoint
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                # API key authentication
│   │   │   ├── rate_limit.py          # Rate limiting
│   │   │   └── logging.py             # Request/response logging
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── project.py             # Project schemas
│   │   │   ├── artifact.py            # Artifact schemas
│   │   │   └── workflow.py            # Workflow schemas
│   │   ├── services/                  # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── project_service.py     # Project management operations
│   │   │   ├── artifact_service.py    # Artifact storage & retrieval
│   │   │   └── workflow_service.py    # Workflow orchestration
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── openai_client.py       # OpenAI API client wrapper
│   │       └── helpers.py             # Shared utility functions
│   │
│   ├── agents/                        # AI agent implementations
│   │   ├── __init__.py
│   │   ├── base.py                    # Abstract base agent (ABC)
│   │   ├── schemas.py                 # Agent Pydantic output models
│   │   ├── prompts.py                 # System prompt templates
│   │   ├── requirements_agent.py      # Requirements Agent
│   │   ├── architect_agent.py         # Architect Agent
│   │   ├── developer_agent.py         # Developer Agent
│   │   ├── tester_agent.py            # Tester Agent
│   │   ├── documentation_agent.py     # Documentation Agent
│   │   └── code_review_agent.py       # Code Review Agent
│   │
│   ├── langgraph/                     # LangGraph workflow engine
│   │   ├── __init__.py
│   │   ├── graph.py                   # Workflow graph definition
│   │   ├── state.py                   # State schema (TypedDict)
│   │   ├── nodes.py                   # Node function definitions
│   │   ├── edges.py                   # Conditional edge resolvers
│   │   ├── compiler.py                # Graph compilation
│   │   └── executor.py                # Graph execution with error handling
│   │
│   ├── database/                      # Database layer
│   │   ├── __init__.py
│   │   ├── postgres.py                # PostgreSQL connection & session
│   │   ├── models.py                  # SQLAlchemy ORM models
│   │   ├── migrations/                # Alembic migration scripts
│   │   │   ├── env.py
│   │   │   ├── alembic.ini
│   │   │   └── versions/
│   │   └── chroma.py                  # ChromaDB client & collections
│   │
│   ├── frontend/                      # React + Next.js frontend
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── next.config.js
│   │   ├── tailwind.config.js
│   │   ├── public/
│   │   │   └── favicon.ico
│   │   └── src/
│   │       ├── app/
│   │       │   ├── layout.tsx         # Root layout
│   │       │   ├── page.tsx           # Home / project submission
│   │       │   ├── projects/
│   │       │   │   ├── [id]/
│   │       │   │   │   ├── page.tsx   # Project detail view
│   │       │   │   │   └── preview/
│   │       │   │   │       └── page.tsx # Code preview
│   │       │   │   └── page.tsx       # Project list
│   │       │   └── globals.css
│   │       ├── components/
│   │       │   ├── ProjectForm.tsx     # Idea submission form
│   │       │   ├── WorkflowGraph.tsx   # DAG visualization
│   │       │   ├── ArtifactCard.tsx    # Artifact display card
│   │       │   ├── AgentTimeline.tsx   # Agent execution timeline
│   │       │   └── CodePreviewer.tsx   # Syntax-highlighted code view
│   │       ├── lib/
│   │       │   ├── api.ts             # API client functions
│   │       │   └── types.ts           # TypeScript type definitions
│   │       └── hooks/
│   │           ├── useProject.ts      # Project data hook
│   │           └── useWebSocket.ts    # WebSocket connection hook
│   │
│   └── scripts/                       # Utility scripts
│       ├── seed_data.py               # Database seeding
│       ├── test_workflow.py           # Workflow end-to-end test
│       └── export_project.py          # Project ZIP export
│
├── tests/                             # Test suite
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures & config
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_agents.py             # Agent unit tests
│   │   ├── test_langgraph.py          # Workflow engine tests
│   │   └── test_api.py                # API endpoint tests
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_workflow_e2e.py       # End-to-end workflow tests
│   │   └── test_database.py           # Database integration tests
│   └── fixtures/                      # Test data
│       ├── sample_idea.txt
│       └── mock_agent_responses.json
│
├── docker/                            # Docker configuration
│   ├── Dockerfile.api                 # API service Dockerfile
│   ├── Dockerfile.frontend            # Frontend Dockerfile
│   ├── docker-compose.yml             # Multi-service orchestration
│   └── .dockerignore
│
├── .env.example                       # Environment variable template
├── .gitignore
├── requirements.txt                   # Python dependencies
├── Makefile                           # Common development commands
└── README.md                          # Project overview
```

## Directory Descriptions

| Directory | Purpose |
|-----------|---------|
| `docs/` | All project documentation (SRS, architecture, roadmap) |
| `src/api/` | FastAPI application with routers, middleware, schemas, services |
| `src/agents/` | Six AI agent implementations with base class and prompts |
| `src/langgraph/` | LangGraph state graph, nodes, edges, compilation, execution |
| `src/database/` | PostgreSQL models, ChromaDB client, Alembic migrations |
| `src/frontend/` | Next.js 14 application with TypeScript |
| `src/scripts/` | Development and maintenance scripts |
| `tests/` | Unit, integration, and end-to-end tests |
| `docker/` | Containerization files |
| `checkpoints/` | Automated recovery snapshots |
| `backups/` | Versioned file backups before overwrites |
