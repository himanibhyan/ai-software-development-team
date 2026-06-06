# Architecture Design Document (ADD)

## AI Software Development Team

**Version:** 1.0  
**Date:** 2026-06-06  
**Author:** Senior AI Architect  
**Status:** Draft  

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Submit   │  │ Workflow │  │ Artifact │  │ Project  │   │
│  │ Idea     │  │ Viewer   │  │ Preview  │  │ History  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                    API Gateway (FastAPI)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ /api/v1/ │  │ /api/v1/ │  │ /api/v1/ │  │ /api/v1/ │   │
│  │ projects │  │ workflow │  │ artifacts│  │ auth     │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  LangGraph Orchestrator                       │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │State Mgmt│  │Graph     │  │Edge      │  │Node      │   │
│  │          │  │Compiler  │  │Resolver  │  │Executor  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Agent Layer                                │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Requirements│  │Architect │  │Developer │  │  Tester  │   │
│  │  Agent    │  │  Agent   │  │  Agent   │  │  Agent   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐                                  │
│  │Document. │  │Code Review│                                  │
│  │  Agent   │  │  Agent   │                                  │
│  └──────────┘  └──────────┘                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Infrastructure Layer                        │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │PostgreSQL│  │ ChromaDB │  │   Redis  │  │    S3    │   │
│  │          │  │          │  │  (Cache)  │  │(Artifacts)│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Architecture Principles
- **Separation of Concerns:** Each agent has a single, well-defined responsibility.
- **Stateful Orchestration:** LangGraph manages all workflow state explicitly.
- **Immutable Artifacts:** Once created, agent outputs are versioned and never mutated.
- **Observability:** Every agent action is logged with timing, token usage, and status.
- **Resilience:** Failures in individual agents do not cascade; workflow can be resumed.

---

## 2. Component Architecture

### 2.1 FastAPI Application Layer

```
fastapi_app/
├── main.py                    # Application entry point, middleware
├── config.py                  # Environment-based configuration
├── dependencies.py            # Dependency injection
├── routers/
│   ├── __init__.py
│   ├── projects.py            # Project CRUD endpoints
│   ├── workflow.py            # Workflow control endpoints
│   ├── artifacts.py           # Artifact retrieval endpoints
│   └── health.py             # Health check
├── middleware/
│   ├── auth.py                # API key authentication
│   ├── rate_limit.py          # Rate limiting
│   └── logging.py            # Request/response logging
└── exceptions.py              # Global exception handlers
```

### 2.2 LangGraph Workflow Engine

```
langgraph_engine/
├── __init__.py
├── graph.py                   # Workflow graph definition
├── state.py                   # State schema (TypedDict)
├── nodes/
│   ├── __init__.py
│   ├── requirements_node.py
│   ├── architect_node.py
│   ├── developer_node.py
│   ├── tester_node.py
│   ├── documentation_node.py
│   └── code_review_node.py
├── edges.py                   # Conditional edge logic
├── compiler.py                # Graph compilation
└── executor.py                # Graph execution with error handling
```

### 2.3 Agent Layer

```
agents/
├── __init__.py
├── base.py                    # Abstract base agent class
├── requirements_agent.py     # Requirements analysis
├── architect_agent.py        # System design
├── developer_agent.py        # Code generation
├── tester_agent.py           # Test generation
├── documentation_agent.py    # Documentation generation
└── code_review_agent.py      # Quality review
```

Each agent follows this pattern:
```python
class BaseAgent(ABC):
    model: str = "gpt-4o"
    temperature: float = 0.2
    max_tokens: int = 4096

    @abstractmethod
    def system_prompt(self) -> str: ...

    @abstractmethod
    def parse_response(self, response: str) -> BaseModel: ...

    async def execute(self, context: AgentContext) -> BaseModel:
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": self.format_input(context)}
        ]
        response = await openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return self.parse_response(response.choices[0].message.content)
```

### 2.4 Agent Communication Design

#### 2.4.1 State Schema (LangGraph TypedDict)
```python
class ProjectState(TypedDict):
    project_id: str
    idea: str
    status: Literal["pending", "in_progress", "completed", "failed"]
    current_iteration: int
    max_iterations: int

    # Agent Artifacts
    requirements: Optional[RequirementsDocument]
    architecture: Optional[ArchitectureDocument]
    source_code: Optional[SourceCodeArtifact]
    test_suite: Optional[TestSuite]
    documentation: Optional[TechnicalDocumentation]

    # Review
    review_report: Optional[ReviewReport]
    review_approved: bool

    # Execution
    errors: List[str]
    timeline: List[TimelineEvent]
    agent_feedback: Optional[str]
```

#### 2.4.2 Data Flow
```
User Idea
    │
    ▼
[Requirements Agent] ──► RequirementsDocument
    │
    ▼
[Architect Agent] ──► ArchitectureDocument
    │
    ▼
[Developer Agent] ──► SourceCodeArtifact
    │
    ├──────────────────┐
    ▼                  ▼
[Tester Agent]    [Code Review Agent]
    │                  │
    │                  ▼
    │           ReviewReport (issues?)
    │                  │
    │           ┌──────┴──────┐
    │           │ Yes         │ No
    │           ▼             │
    │      Loop back to       │
    │      relevant agent     │
    │           │             │
    └───────────┴─────────────┘
                              │
                              ▼
                 [Documentation Agent]
                              │
                              ▼
                    TechnicalDocumentation
                              │
                              ▼
                     Final Project Output
```

### 2.5 LangGraph Workflow Design

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(ProjectState)

# Add nodes
workflow.add_node("requirements", requirements_agent.execute)
workflow.add_node("architect", architect_agent.execute)
workflow.add_node("developer", developer_agent.execute)
workflow.add_node("tester", tester_agent.execute)
workflow.add_node("code_review", code_review_agent.execute)
workflow.add_node("documentation", documentation_agent.execute)

# Add edges
workflow.add_edge("requirements", "architect")
workflow.add_edge("architect", "developer")
workflow.add_edge("developer", "tester")
workflow.add_edge("tester", "code_review")

# Conditional edge: loop back if review fails
workflow.add_conditional_edges(
    "code_review",
    decide_next_agent,  # Returns "documentation", "developer", or "architect"
    {
        "documentation": "documentation",
        "developer": "developer",
        "architect": "architect",
    }
)

workflow.add_edge("documentation", END)

# Set entry point
workflow.set_entry_point("requirements")

# Compile
app = workflow.compile()
```

### 2.6 Conditional Edge Logic
```python
def decide_next_agent(state: ProjectState) -> str:
    if state.review_approved:
        return "documentation"
    if state.current_iteration >= state.max_iterations:
        return "documentation"  # Force proceed after max iterations
    if state.review_report.affects_architecture:
        return "architect"
    return "developer"
```

---

## 3. Database Design

### 3.1 Entity-Relationship Diagram
```
┌─────────────┐       ┌─────────────┐       ┌──────────────┐
│  projects   │───────│  artifacts  │       │ workflow_logs│
├─────────────┤ 1:N   ├─────────────┤       ├──────────────┤
│ id (PK)     │       │ id (PK)     │       │ id (PK)      │
│ idea        │       │ project_id  │       │ project_id   │
│ status      │       │ agent_type  │       │ agent_type   │
│ current_agent│      │ artifact_type│      │ action       │
│ iteration   │       │ content     │       │ status       │
│ created_at  │       │ version     │       │ duration_ms  │
│ updated_at  │       │ created_at  │       │ created_at   │
└─────────────┘       └─────────────┘       └──────────────┘
```

### 3.2 Indexes
```sql
CREATE INDEX idx_artifacts_project ON artifacts(project_id);
CREATE INDEX idx_artifacts_type ON artifacts(agent_type, artifact_type);
CREATE INDEX idx_workflow_logs_project ON workflow_logs(project_id);
CREATE INDEX idx_workflow_logs_agent ON workflow_logs(agent_type, status);
CREATE INDEX idx_projects_status ON projects(status);
```

---

## 4. API Design

### 4.1 OpenAPI Specification (Summary)

#### POST /api/v1/projects
```json
{
  "summary": "Create a new project from a software idea",
  "request_body": {
    "content": {
      "application/json": {
        "schema": {
          "type": "object",
          "properties": {
            "idea": {"type": "string", "description": "The software idea in natural language"},
            "max_iterations": {"type": "integer", "default": 3}
          },
          "required": ["idea"]
        }
      }
    }
  },
  "responses": {
    "201": {
      "description": "Project created",
      "content": {
        "application/json": {
          "schema": {
            "$ref": "#/components/schemas/ProjectResponse"
          }
        }
      }
    }
  }
}
```

#### WebSocket /ws/v1/projects/{id}
- **Purpose:** Real-time workflow progress updates.
- **Message Format:**
```json
{
  "type": "agent_update",
  "data": {
    "agent": "requirements",
    "status": "completed",
    "duration_ms": 4500
  }
}
```

---

## 5. Security Architecture

### 5.1 Authentication
- API key-based authentication via `X-API-Key` header.
- Keys stored as hashed values in PostgreSQL.
- Rate limiting per key using Redis sliding window.

### 5.2 Data Protection
- All API traffic over HTTPS.
- OpenAI API keys stored in environment variables, never exposed.
- Artifact content stored in JSONB columns (no file system I/O for small projects).
- Large artifacts (>10MB) stored in S3-compatible object storage.

### 5.3 Prompt Security
- Input sanitization striping control characters and excessive length.
- Prompt injection detection using pattern matching.
- Agent output validation against Pydantic schemas.

---

## 6. Deployment Architecture

### 6.1 Docker Compose Layout
```yaml
services:
  api:
    build: ./src/api
    ports: ["8000:8000"]
    depends_on: [postgres, chromadb, redis]

  frontend:
    build: ./src/frontend
    ports: ["3000:3000"]
    depends_on: [api]

  postgres:
    image: postgres:16
    volumes: [postgres_data:/var/lib/postgresql/data]

  chromadb:
    image: chromadb/chroma:latest
    volumes: [chroma_data:/chroma/chroma]

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
  chroma_data:
```

### 6.2 Scaling Strategy
- API layer: Horizontal scaling behind Nginx reverse proxy.
- Agent workers: Task queue (Celery/Redis) for agent execution offloading.
- Database: Read replicas for artifact queries, primary for writes.

---

## 7. Monitoring & Observability

### 7.1 Metrics
- **Agent Metrics:** Execution time, token usage, success/failure rate per agent type.
- **Workflow Metrics:** Total duration, iterations per project, approval rate.
- **System Metrics:** API latency, error rate, database connection pool usage.

### 7.2 Logging
- Structured JSON logging with correlation IDs.
- Log levels: DEBUG (agent prompts/responses), INFO (workflow transitions), ERROR (failures).
- Log aggregation via Loki or ELK stack.

### 7.3 Tracing
- OpenTelemetry distributed tracing across agent calls.
- LangGraph callback integration for automatic span creation.
