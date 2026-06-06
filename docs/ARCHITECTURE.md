# Architecture Design Document
## AI Software Development Team v1.0

---

## 1. System Overview

The system uses a **Supervisor + Worker** pattern built on LangGraph's `StateGraph`. A single orchestrator agent manages the pipeline, while specialized worker agents execute domain-specific tasks. All inter-agent communication flows through a shared, versioned state object.

```
┌──────────────────────────────────────────────────────┐
│                    User Interface                      │
│  (Next.js Web UI OR FastAPI REST Client / WebSocket)  │
└──────────────┬───────────────────────────┬────────────┘
               │ HTTP/WS                    │ HTTP/WS
               ▼                            ▼
┌──────────────────────────────────────────────────────┐
│                   FastAPI Gateway                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ REST API │  │WebSocket │  │ Auth / Rate Limit   │  │
│  └──────────┘  └──────────┘  └────────────────────┘  │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│               LangGraph Orchestrator                   │
│  ┌─────────────────────────────────────────────────┐  │
│  │  StateGraph (nodes = agents, edges = pipeline)   │  │
│  │                                                   │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │  │
│  │  │Requirements│→│ Architect │→│ Developer│       │  │
│  │  └──────────┘  └──────────┘  └─────┬────┘       │  │
│  │         ┌──────────────────────────┼──┐          │  │
│  │         ▼                          ▼  ▼          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │  │
│  │  │  Tester   │  │CodeReview│  │  Docs    │       │  │
│  │  └──────────┘  └──────────┘  └──────────┘       │  │
│  └─────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐
│  PostgreSQL   │ │ ChromaDB │ │ File     │
│  (Artifacts,  │ │ (Vectors, │ │ System   │
│   State, Logs)│ │  Memory)  │ │ (Output) │
└──────────────┘ └──────────┘ └──────────┘
```

---

## 2. LangGraph Workflow Design

### 2.1 StateGraph Definition

```python
class GraphState(TypedDict):
    # Input
    idea: str
    constraints: Optional[Dict]
    
    # Generated Artifacts
    requirements: Optional[RequirementsDoc]
    architecture: Optional[ArchitectureDoc]
    source_code: Optional[ProjectTree]
    test_suite: Optional[TestSuite]
    documentation: Optional[Documentation]
    review_report: Optional[CodeReviewReport]
    
    # Metadata
    project_id: str
    status: AgentStatus  # enum: PENDING, RUNNING, COMPLETED, FAILED
    current_agent: AgentType
    errors: List[AgentError]
    start_time: datetime
    end_time: Optional[datetime]
    session_id: str
```

### 2.2 Graph Pipeline

```
Node Sequence:
  [START] → validate_input → requirements_agent → architect_agent 
  → developer_agent → parallel[tester_agent, codereview_agent] 
  → documentation_agent → persistence_node → [END]

Conditional Edges:
  - Any agent fails → error_handler → retry_logic → previous_agent OR [END]
  - Code review score < threshold → developer_agent (feedback loop)
```

### 2.3 Agent Definitions

**Requirements Agent**
- System Prompt: "You are a Senior Product Manager..."
- Tools: ChromaDB similarity search (lookup similar past projects)
- Output: Structured RequirementsDoc (Pydantic model)
- Validation: Schema check + hallucination guard (factual consistency)

**Architect Agent**
- System Prompt: "You are a Distinguished Architect..."
- Tools: ChromaDB lookup, file system (read existing templates)
- Output: ArchitectureDoc with diagrams, tech stack, component specs
- Validation: Consistency check with requirements

**Developer Agent**
- System Prompt: "You are a Senior Software Engineer..."
- Tools: Code execution sandbox (syntax check), file system
- Output: ProjectTree (nested Dict[str, str] of file paths→content)
- Validation: AST parse check, dependency resolution

**Tester Agent**
- System Prompt: "You are a QA Lead..."
- Tools: AST parser (identify testable units)
- Output: TestSuite (test files + test configuration)
- Validation: Generated tests reference real functions

**Code Review Agent**
- System Prompt: "You are a Senior Code Reviewer..."
- Tools: AST parser, complexity analyzer
- Output: CodeReviewReport (line comments + summary)
- Validation: Review must reference specific line numbers

**Documentation Agent**
- System Prompt: "You are a Technical Writer..."
- Tools: File system
- Output: Documentation (README, API docs, setup guide)
- Validation: All required sections present

### 2.4 State Management

Every state transition is atomic:
1. Agent receives current state (read-only snapshot)
2. Agent produces output
3. Orchestrator validates output schema
4. State is updated immutably (new revision)
5. Full state snapshot persisted to PostgreSQL (audit trail)

State versioning via `project_id + revision_number`.

---

## 3. Database Schema (PostgreSQL)

### 3.1 Entity Relationship

```
┌─────────────────────┐
│      projects       │
├─────────────────────┤
│ id (UUID PK)        │──┐
│ idea (TEXT)          │  │
│ constraints (JSONB)  │  │
│ status (ENUM)        │  │
│ created_at (TIMESTAMPTZ)│
│ updated_at (TIMESTAMPTZ)│
└─────────────────────┘  │
                         │
┌──────────────────────┐ │
│   project_artifacts   │ │
├──────────────────────┤ │
│ id (UUID PK)          │ │
│ project_id (UUID FK) │◄┘
│ agent_type (VARCHAR)  │
│ artifact_type (VARCHAR)│
│ content (JSONB)        │
│ markdown (TEXT)        │
│ revision (INT)         │
│ created_at (TIMESTAMPTZ)│
└──────────────────────┘

┌──────────────────────┐
│   agent_executions    │
├──────────────────────┤
│ id (UUID PK)          │
│ project_id (UUID FK) │
│ agent_type (VARCHAR)  │
│ status (ENUM)         │
│ input_tokens (INT)    │
│ output_tokens (INT)   │
│ duration_ms (INT)     │
│ error (JSONB)         │
│ started_at (TIMESTAMPTZ)│
│ ended_at (TIMESTAMPTZ) │
└──────────────────────┘

┌──────────────────────┐
│   feedback_entries    │
├──────────────────────┤
│ id (UUID PK)          │
│ project_id (UUID FK) │
│ agent_type (VARCHAR)  │
│ feedback (TEXT)       │
│ created_at (TIMESTAMPTZ)│
└──────────────────────┘
```

---

## 4. API Design

### 4.1 REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/projects` | Submit new software idea |
| GET | `/api/v1/projects/{id}` | Get project status & artifacts |
| GET | `/api/v1/projects` | List all projects (paginated) |
| POST | `/api/v1/projects/{id}/refine` | Submit feedback for refinement |
| DELETE | `/api/v1/projects/{id}` | Delete project |
| POST | `/api/v1/projects/{id}/export` | Export to GitHub |
| GET | `/api/v1/projects/{id}/stream` | SSE stream of agent progress |

### 4.2 WebSocket Endpoints

| Path | Description |
|------|-------------|
| `/ws/v1/projects/{id}` | Real-time agent status updates |

### 4.3 Request/Response Schemas

**POST /api/v1/projects**
```json
{
  "idea": "Build a REST API for a todo app with user auth",
  "constraints": {
    "tech_stack": ["python", "fastapi", "postgresql"],
    "output_format": "python_project"
  }
}
→ 201
{
  "project_id": "uuid-here",
  "status": "PENDING",
  "status_url": "/api/v1/projects/uuid-here"
}
```

**GET /api/v1/projects/{id}**
```json
{
  "project_id": "uuid-here",
  "status": "COMPLETED",
  "artifacts": {
    "requirements": { "title": "...", "sections": [...] },
    "architecture": { "title": "...", "components": [...] },
    "source_code": { "files": {"main.py": "content...", ...} },
    "tests": { "files": {"test_main.py": "content...", ...} },
    "documentation": { "readme": "...#", ... },
    "review": { "score": 8.5, "comments": [...] }
  },
  "execution_time_ms": 245000,
  "token_usage": { "prompt": 45000, "completion": 12000 }
}
```

---

## 5. Agent Communication Design

### 5.1 Pattern: Shared State (Blackboard)

All agents read from and write to a single `GraphState` object. No direct agent-to-agent messaging:

```
Agent A ──write──▶ GraphState ──read──▶ Agent B
                     │
                     ▼
               PostgreSQL
              (persistence)
```

### 5.2 Communication Protocol

| Aspect | Detail |
|--------|--------|
| Medium | In-memory Python dict (LangGraph StateGraph) |
| Serialization | Pydantic models → JSON |
| Validation | Each agent validates its output against a schema |
| Security | No agent can read another agent's intermediate state |
| Audit | Every state mutation is logged with timestamp + agent ID |

### 5.3 Error Communication

Errors propagate upward:
1. Agent timeout → Orchestrator retries (3 attempts)
2. Schema validation failure → Re-prompt with fix instruction
3. LLM hallucination (low confidence) → Re-prompt with stricter constraints
4. Irrecoverable error → State marked FAILED, user notified

---

## 6. RAG & Memory Architecture

### 6.1 ChromaDB Collections

| Collection | Content | Use |
|-----------|---------|-----|
| `past_projects` | Previous project artifacts | Similar project retrieval |
| `code_templates` | Boilerplate code patterns | Code generation acceleration |
| `agent_memory` | Agent-specific learnings | Cross-session improvement |

### 6.2 Embedding Pipeline

```
Artifact Generated → Chunking (by section/file) → Embedding (OpenAI text-embedding-3-small)
→ Store in ChromaDB with metadata (project_id, agent_type, artifact_type)
→ Retrieval: top-k cosine similarity (k=3)
```

---

## 7. Deployment Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Docker Compose                      │
│                                                        │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │  FastAPI  │  │  Next.js  │  │  Celery Worker     │  │
│  │  (3 pods) │  │  (2 pods) │  │  (auto-scale)      │  │
│  └─────┬────┘  └─────┬────┘  └──────────┬─────────┘  │
│        │              │                   │            │
│  ┌─────┴──────────────┴───────────────────┴────────┐  │
│  │                  Nginx / Traefik                  │  │
│  └──────────────────────┬──────────────────────────┘  │
│                         │                              │
│  ┌──────────────────────┴──────────────────────────┐  │
│  │                  Redis (Pub/Sub + Queue)          │  │
│  └──────────────────────┬──────────────────────────┘  │
│                         │                              │
│  ┌──────────┐  ┌────────┴──────┐  ┌──────────┐       │
│  │PostgreSQL│  │   ChromaDB    │  │   S3/GCS │       │
│  └──────────┘  └───────────────┘  └──────────┘       │
└──────────────────────────────────────────────────────┘
```

---

## 8. Security Design

### 8.1 Authentication
- API key-based auth for programmatic access
- JWT-based auth for web UI sessions
- OpenAI API key stored as environment variable (never exposed)

### 8.2 Rate Limiting
- 10 requests/minute per API key
- 1 concurrent generation per user

### 8.3 Prompt Injection Prevention
- Input sanitization (strip control characters, limit length)
- System prompt boundary markers
- Output content filtering (PII redaction)

---

## 9. Observability

### 9.1 Metrics (Prometheus)
- Agent execution duration (histogram)
- Token usage per agent (counter)
- Generation success rate (gauge)
- Queue depth (gauge)

### 9.2 Logging (Structured JSON)
| Field | Description |
|-------|-------------|
| `event` | `agent_start`, `agent_complete`, `agent_error` |
| `project_id` | UUID |
| `agent_type` | Role name |
| `duration_ms` | Execution time |
| `token_usage` | {prompt, completion} |
| `error` | Error details if applicable |

### 9.3 Tracing (OpenTelemetry)
- Distributed trace across agent pipeline
- Each agent = 1 span
- LLM calls = sub-spans with token counts
