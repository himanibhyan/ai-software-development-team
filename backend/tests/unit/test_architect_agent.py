from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agents.architect_agent import ArchitectAgent
from app.graph.state import create_initial_state
from app.models.domain.enums import AgentType
from app.models.domain.project import (
    APISpec,
    APIEndpoint,
    ArchitectureDoc,
    ComponentSpec,
    DatabaseDesign,
    DatabaseTable,
    FolderEntry,
    FolderStructure,
)


class TestArchitectureDocSchema:
    """Test the ArchitectureDoc Pydantic schema."""

    def test_valid_architecture_doc(self):
        doc = ArchitectureDoc(
            title="FoodExpress Architecture",
            overview="A scalable microservices architecture for the FoodExpress food delivery platform.",
            architecture_pattern="Microservices",
            components=[
                ComponentSpec(
                    name="API Gateway",
                    description="Entry point for all client requests",
                    technology="FastAPI 0.111",
                    responsibilities=["Request routing", "Authentication", "Rate limiting"],
                    dependencies=[],
                ),
                ComponentSpec(
                    name="Order Service",
                    description="Manages order lifecycle",
                    technology="FastAPI 0.111",
                    responsibilities=["Create orders", "Update order status", "Validate orders"],
                    dependencies=["API Gateway", "Database"],
                ),
                ComponentSpec(
                    name="Notification Service",
                    description="Sends push and email notifications",
                    technology="Celery 5.4",
                    responsibilities=["Send push notifications", "Send email alerts"],
                    dependencies=["Order Service"],
                ),
            ],
            data_flow=[
                {"step": "1", "description": "Client sends request to API Gateway"},
                {"step": "2", "description": "Gateway authenticates and routes to Order Service"},
                {"step": "3", "description": "Order Service processes and persists order"},
                {"step": "4", "description": "Notification Service sends confirmation"},
            ],
            tech_stack={
                "language": "Python 3.12",
                "framework": "FastAPI 0.111",
                "database": "PostgreSQL 16",
                "cache": "Redis 7.2",
                "message_queue": "RabbitMQ 3.13",
            },
            deployment_strategy="Docker containers on Kubernetes with auto-scaling and blue-green deployments.",
            security_considerations=[
                "JWT authentication for all endpoints",
                "TLS 1.3 encryption in transit",
                "Secrets managed via AWS Secrets Manager",
            ],
        )
        assert doc.title == "FoodExpress Architecture"
        assert len(doc.components) == 3
        assert len(doc.tech_stack) == 5

    def test_valid_doc_with_all_fields(self):
        doc = ArchitectureDoc(
            title="Full Architecture",
            overview="Complete architecture with all optional fields populated for testing purposes.",
            architecture_pattern="Modular Monolith",
            components=[
                ComponentSpec(
                    name="Web Server",
                    description="Serves HTTP requests and static files",
                    technology="Nginx 1.25",
                    responsibilities=["Serve static files", "Reverse proxy", "SSL termination"],
                    dependencies=[],
                ),
                ComponentSpec(
                    name="Application Server",
                    description="Hosts the business logic",
                    technology="Gunicorn 22 with FastAPI 0.111",
                    responsibilities=["Handle API requests", "Business logic execution", "Session management"],
                    dependencies=["Web Server", "Database"],
                ),
                ComponentSpec(
                    name="Database",
                    description="Primary data store",
                    technology="PostgreSQL 16",
                    responsibilities=["Data persistence", "Query execution", "Data integrity"],
                    dependencies=[],
                ),
            ],
            data_flow=[
                {"step": "1", "description": "Request enters via Web Server"},
                {"step": "2", "description": "Web Server proxies to Application Server"},
                {"step": "3", "description": "Application Server queries Database"},
                {"step": "4", "description": "Response flows back through the chain"},
                {"step": "5", "description": "Client receives response"},
            ],
            tech_stack={
                "language": "Python 3.12",
                "framework": "FastAPI 0.111",
                "database": "PostgreSQL 16",
                "cache": "Redis 7.2",
                "message_queue": "RabbitMQ 3.13",
                "frontend": "React 18",
            },
            deployment_strategy="Docker Compose for development, single VM for production with systemd.",
            security_considerations=[
                "OAuth 2.0 for API access",
                "Input validation on all endpoints",
                "Rate limiting per IP",
                "SQL injection prevention",
            ],
            database_design=DatabaseDesign(
                engine="PostgreSQL 16",
                tables=[
                    DatabaseTable(
                        name="users",
                        columns=[
                            {"name": "id", "type": "UUID", "constraints": "PRIMARY KEY DEFAULT gen_random_uuid()"},
                            {"name": "email", "type": "VARCHAR(255)", "constraints": "UNIQUE NOT NULL"},
                            {"name": "created_at", "type": "TIMESTAMPTZ", "constraints": "NOT NULL DEFAULT NOW()"},
                        ],
                        description="Stores user accounts",
                        relationships=["has_many -> orders"],
                    ),
                    DatabaseTable(
                        name="orders",
                        columns=[
                            {"name": "id", "type": "UUID", "constraints": "PRIMARY KEY DEFAULT gen_random_uuid()"},
                            {"name": "user_id", "type": "UUID", "constraints": "NOT NULL REFERENCES users(id)"},
                            {"name": "amount", "type": "DECIMAL(10,2)", "constraints": "NOT NULL"},
                            {"name": "status", "type": "VARCHAR(50)", "constraints": "NOT NULL DEFAULT 'pending'"},
                        ],
                        description="Stores order records",
                        relationships=["belongs_to -> users"],
                    ),
                ],
                orm="SQLAlchemy 2.0",
                migration_tool="Alembic 1.13",
            ),
            api_spec=APISpec(
                protocol="REST",
                base_url="/api/v1",
                endpoints=[
                    APIEndpoint(path="/auth/login", method="POST", description="User login", auth_required=False),
                    APIEndpoint(path="/users/me", method="GET", description="Get current user", auth_required=True),
                    APIEndpoint(path="/orders", method="GET", description="List user orders", auth_required=True),
                ],
                auth_method="JWT",
            ),
            folder_structure=FolderStructure(
                root="myproject",
                entries=[
                    FolderEntry(name="backend", type="directory", children=[
                        FolderEntry(name="app", type="directory", description="Source code"),
                        FolderEntry(name="tests", type="directory", description="Tests"),
                    ]),
                    FolderEntry(name="frontend", type="directory", children=[
                        FolderEntry(name="src", type="directory"),
                    ]),
                    FolderEntry(name="docker-compose.yml", type="file", description="Orchestration"),
                ],
            ),
        )
        assert doc.database_design is not None
        assert doc.api_spec is not None
        assert doc.folder_structure is not None
        assert len(doc.database_design.tables) == 2
        assert len(doc.api_spec.endpoints) == 3

    def test_too_few_components(self):
        with pytest.raises(ValidationError):
            ArchitectureDoc(
                title="Bad",
                overview="Too few components",
                architecture_pattern="Layered",
                components=[
                    ComponentSpec(name="Only", description="Just one component which is not enough", technology="Python", responsibilities=["Do things"], dependencies=[]),
                ],
                data_flow=[{"step": "1", "description": "Something happens"}],
                tech_stack={"lang": "Python"},
                deployment_strategy="Simple",
                security_considerations=["Auth"],
            )

    def test_component_spec_validation(self):
        with pytest.raises(ValidationError):
            ComponentSpec(
                name="",
                description="Short",
                technology="",
                responsibilities=[],
            )

    def test_doc_frozen(self):
        doc = ArchitectureDoc(
            title="Test Arch",
            overview="A test architecture document for frozen validation testing purposes.",
            architecture_pattern="Layered",
            components=[
                ComponentSpec(
                    name="API",
                    description="API layer that handles all HTTP requests and responses.",
                    technology="FastAPI 0.111",
                    responsibilities=["Handle requests", "Validate input"],
                    dependencies=[],
                ),
                ComponentSpec(
                    name="Service",
                    description="Business logic and core application processing layer.",
                    technology="Python 3.12",
                    responsibilities=["Business logic", "Data processing"],
                    dependencies=["API"],
                ),
                ComponentSpec(
                    name="Database",
                    description="Persistence layer for data storage and retrieval operations.",
                    technology="PostgreSQL 16",
                    responsibilities=["Store data", "Run queries"],
                    dependencies=[],
                ),
            ],
            data_flow=[
                {"step": "1", "description": "Request to API"},
                {"step": "2", "description": "API calls Service"},
                {"step": "3", "description": "Service queries Database"},
                {"step": "4", "description": "Response returned"},
            ],
            tech_stack={
                "language": "Python 3.12",
                "framework": "FastAPI 0.111",
                "database": "PostgreSQL 16",
                "cache": "Redis 7.2",
                "message_queue": "RabbitMQ 3.13",
            },
            deployment_strategy="Docker containers with docker-compose for development and Kubernetes for production.",
            security_considerations=[
                "JWT authentication",
                "TLS encryption",
                "Rate limiting",
            ],
        )
        with pytest.raises(ValidationError):
            doc.title = "Changed"


class TestArchitectAgent:
    """Tests for the ArchitectAgent itself."""

    def test_agent_type(self):
        agent = ArchitectAgent(llm_service=None)
        assert agent.agent_type == AgentType.ARCHITECT

    def test_system_prompt_is_string(self):
        agent = ArchitectAgent(llm_service=None)
        prompt = agent.system_prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 500
        assert "Distinguished Software Architect" in prompt

    def test_output_model_is_architecture_doc(self):
        agent = ArchitectAgent(llm_service=None)
        assert agent.output_model == ArchitectureDoc

    def test_state_field(self):
        agent = ArchitectAgent(llm_service=None)
        assert agent._state_field() == "architecture"

    def test_build_user_prompt_includes_idea(self, sample_idea: str):
        agent = ArchitectAgent(llm_service=None)
        state = create_initial_state(idea=sample_idea)
        prompt = agent.build_user_prompt(state)
        assert sample_idea in prompt
        assert "components" in prompt.lower() or "architecture" in prompt.lower()

    def test_build_user_prompt_includes_requirements(self, sample_idea: str):
        agent = ArchitectAgent(llm_service=None)
        state = create_initial_state(idea=sample_idea)
        state["requirements"] = {
            "title": "Test Project",
            "purpose": "Testing purposes with enough detail to pass validation.",
            "scope": "In scope: testing. Out of scope: nothing.",
            "functional_requirements": [
                {"id": "FR-01", "description": "Users shall be able to register.", "priority": "P0"},
                {"id": "FR-02", "description": "Users shall be able to log in.", "priority": "P0"},
                {"id": "FR-03", "description": "Users shall be able to create items.", "priority": "P0"},
            ],
            "non_functional_requirements": [
                {"id": "NFR-01", "description": "APIs respond under 300ms.", "category": "performance"},
                {"id": "NFR-02", "description": "All data encrypted at rest.", "category": "security"},
                {"id": "NFR-03", "description": "99.9% uptime.", "category": "availability"},
                {"id": "NFR-04", "description": "Scale to 10k users.", "category": "scalability"},
            ],
            "user_stories": [],
            "constraints": ["Must use Python"],
            "assumptions": ["Internet available"],
        }
        prompt = agent.build_user_prompt(state)
        assert "FR-01" in prompt
        assert "NFR-01" in prompt
        assert "Test Project" in prompt

    def test_build_user_prompt_includes_constraints(self, sample_idea: str):
        agent = ArchitectAgent(llm_service=None)
        constraints = {"tech_stack": ["python", "fastapi"], "budget": "low"}
        state = create_initial_state(idea=sample_idea, constraints=constraints)
        prompt = agent.build_user_prompt(state)
        assert "tech_stack" in prompt

    def test_validate_output_passes_valid_doc(self):
        agent = ArchitectAgent(llm_service=None)
        doc = ArchitectureDoc(
            title="Test Architecture",
            overview="A comprehensive test architecture with all required elements for validation purposes.",
            architecture_pattern="Microservices",
            components=[
                ComponentSpec(
                    name="Gateway",
                    description="API Gateway handling all incoming HTTP requests and authentication.",
                    technology="FastAPI 0.111",
                    responsibilities=["Route requests", "Authenticate users", "Rate limit"],
                    dependencies=[],
                ),
                ComponentSpec(
                    name="Core API",
                    description="Core business logic service for primary application functionality.",
                    technology="FastAPI 0.111",
                    responsibilities=["Process business logic", "Manage data", "Handle errors"],
                    dependencies=["Gateway"],
                ),
                ComponentSpec(
                    name="Worker",
                    description="Background task processor for async job execution and scheduling.",
                    technology="Celery 5.4",
                    responsibilities=["Process async jobs", "Send notifications"],
                    dependencies=["Core API"],
                ),
            ],
            data_flow=[
                {"step": "1", "description": "Client sends request to Gateway"},
                {"step": "2", "description": "Gateway authenticates and forwards to Core API"},
                {"step": "3", "description": "Core API processes and persists data"},
                {"step": "4", "description": "Worker picks up async tasks from queue"},
            ],
            tech_stack={
                "language": "Python 3.12",
                "framework": "FastAPI 0.111",
                "database": "PostgreSQL 16",
                "cache": "Redis 7.2",
                "message_queue": "RabbitMQ 3.13",
            },
            deployment_strategy="Docker containers on Kubernetes with horizontal pod auto-scaling based on CPU utilization.",
            security_considerations=[
                "JWT token authentication for all API endpoints",
                "TLS 1.3 for all inter-service communication",
                "Secrets managed via HashiCorp Vault",
            ],
        )
        result = agent._validate_output(doc)
        assert result is doc

    def test_validate_output_rejects_few_components(self):
        agent = ArchitectAgent(llm_service=None)
        doc = ArchitectureDoc(
            title="Bad",
            overview="Too few components for the architecture validation test case scenario here.",
            architecture_pattern="Layered",
            components=[
                ComponentSpec(
                    name="Only One",
                    description="Single component that fails minimum validation check requirement.",
                    technology="Python",
                    responsibilities=["Do everything"],
                    dependencies=[],
                ),
            ],
            data_flow=[{"step": "1", "description": "Something happens"}],
            tech_stack={"lang": "Python", "framework": "FastAPI"},
            deployment_strategy="Simple container deployment strategy for testing the validation logic here.",
            security_considerations=["Auth"],
        )
        with pytest.raises(ValueError, match="Too few components"):
            agent._validate_output(doc)

    def test_validate_output_rejects_duplicate_components(self):
        agent = ArchitectAgent(llm_service=None)
        doc = ArchitectureDoc(
            title="Test",
            overview="Testing duplicate component name validation in the architecture agent.",
            architecture_pattern="Layered",
            components=[
                ComponentSpec(
                    name="Auth Service",
                    description="Authentication service for user login and registration handling.",
                    technology="FastAPI 0.111",
                    responsibilities=["Handle login", "Handle registration"],
                    dependencies=[],
                ),
                ComponentSpec(
                    name="Auth Service",
                    description="Duplicate authentication service that should fail validation.",
                    technology="FastAPI 0.111",
                    responsibilities=["Handle passwords", "Issue tokens"],
                    dependencies=[],
                ),
                ComponentSpec(
                    name="Order Service",
                    description="Order management service for processing customer orders placed online.",
                    technology="FastAPI 0.111",
                    responsibilities=["Create orders", "List orders"],
                    dependencies=["Auth Service"],
                ),
            ],
            data_flow=[
                {"step": "1", "description": "Request to auth"},
                {"step": "2", "description": "Auth validates token"},
                {"step": "3", "description": "Order service processes"},
                {"step": "4", "description": "Response sent back"},
            ],
            tech_stack={
                "language": "Python 3.12",
                "framework": "FastAPI 0.111",
                "database": "PostgreSQL 16",
                "cache": "Redis 7.2",
                "message_queue": "RabbitMQ 3.13",
            },
            deployment_strategy="Docker Compose for development, AWS ECS for production with auto-scaling enabled.",
            security_considerations=[
                "JWT for auth",
                "TLS encryption",
                "Rate limiting per client",
            ],
        )
        with pytest.raises(ValueError, match="Duplicate component name"):
            agent._validate_output(doc)

    def test_validate_output_rejects_vague_tech(self):
        agent = ArchitectAgent(llm_service=None)
        doc = ArchitectureDoc(
            title="Test",
            overview="Testing vague technology validation check in the architecture agent process.",
            architecture_pattern="Layered",
            components=[
                ComponentSpec(
                    name="API",
                    description="API layer handling all HTTP request routing for the application.",
                    technology="some database",
                    responsibilities=["Handle requests", "Route requests"],
                    dependencies=[],
                ),
                ComponentSpec(
                    name="Service",
                    description="Business logic layer for processing all application operations.",
                    technology="Python",
                    responsibilities=["Process logic", "Validate data"],
                    dependencies=["API"],
                ),
                ComponentSpec(
                    name="Database",
                    description="Data persistence layer for storing all application state and records.",
                    technology="PostgreSQL 16",
                    responsibilities=["Store data", "Run queries"],
                    dependencies=[],
                ),
            ],
            data_flow=[
                {"step": "1", "description": "Request to API"},
                {"step": "2", "description": "API calls Service"},
                {"step": "3", "description": "Service queries DB"},
                {"step": "4", "description": "Response returned"},
            ],
            tech_stack={
                "language": "Python 3.12",
                "framework": "FastAPI 0.111",
                "database": "PostgreSQL 16",
                "cache": "Redis 7.2",
                "message_queue": "RabbitMQ 3.13",
            },
            deployment_strategy="Docker based deployment with horizontal scaling for production workloads.",
            security_considerations=[
                "JWT auth",
                "TLS encryption",
                "Rate limiting",
            ],
        )
        with pytest.raises(ValueError, match="vague technology|vague"):
            agent._validate_output(doc)

    def test_validate_output_rejects_missing_language_in_tech_stack(self):
        agent = ArchitectAgent(llm_service=None)
        doc = ArchitectureDoc(
            title="Test",
            overview="Testing missing tech stack categories validation in the architecture agent.",
            architecture_pattern="Layered",
            components=[
                ComponentSpec(
                    name="API",
                    description="API Gateway for routing and authenticating all incoming requests.",
                    technology="FastAPI 0.111",
                    responsibilities=["Route requests", "Auth requests"],
                    dependencies=[],
                ),
                ComponentSpec(
                    name="Service",
                    description="Core service for business logic processing and data management.",
                    technology="Python 3.12",
                    responsibilities=["Business logic", "Data management"],
                    dependencies=["API"],
                ),
                ComponentSpec(
                    name="DB",
                    description="Database service for persistent data storage and retrieval operations.",
                    technology="PostgreSQL 16",
                    responsibilities=["Persist data", "Run queries"],
                    dependencies=[],
                ),
            ],
            data_flow=[
                {"step": "1", "description": "Request to API"},
                {"step": "2", "description": "API calls Service"},
                {"step": "3", "description": "Service queries DB"},
                {"step": "4", "description": "Response flows back"},
            ],
            tech_stack={
                "database": "PostgreSQL 16",
                "cache": "Redis 7.2",
            },
            deployment_strategy="Docker Compose for local dev, Kubernetes for prod with HPA auto-scaling configured.",
            security_considerations=[
                "JWT auth",
                "TLS encryption",
                "Rate limiting",
                "Input validation",
            ],
        )
        with pytest.raises(ValueError, match="Missing required tech stack categories"):
            agent._validate_output(doc)

    def test_validate_output_rejects_few_responsibilities(self):
        agent = ArchitectAgent(llm_service=None)
        doc = ArchitectureDoc(
            title="Test",
            overview="Testing minimum responsibilities validation check per component definition.",
            architecture_pattern="Layered",
            components=[
                ComponentSpec(
                    name="API",
                    description="API layer for HTTP request processing and routing throughout the application.",
                    technology="FastAPI 0.111",
                    responsibilities=["Just one"],  # Only one responsibility
                    dependencies=[],
                ),
                ComponentSpec(
                    name="Service",
                    description="Business logic and processing layer for core application functionality.",
                    technology="Python 3.12",
                    responsibilities=["Process logic", "Validate data"],
                    dependencies=["API"],
                ),
                ComponentSpec(
                    name="DB",
                    description="Database persistence layer for storing all application state and records.",
                    technology="PostgreSQL 16",
                    responsibilities=["Store data", "Query data"],
                    dependencies=[],
                ),
            ],
            data_flow=[
                {"step": "1", "description": "Request to API"},
                {"step": "2", "description": "API to Service"},
                {"step": "3", "description": "Service to DB"},
                {"step": "4", "description": "Response back"},
            ],
            tech_stack={
                "language": "Python 3.12",
                "framework": "FastAPI 0.111",
                "database": "PostgreSQL 16",
                "cache": "Redis 7.2",
                "message_queue": "RabbitMQ 3.13",
            },
            deployment_strategy="Docker Compose for dev environment, Kubernetes with HPA for production deployment.",
            security_considerations=[
                "JWT auth",
                "TLS encryption",
                "Rate limiting",
            ],
        )
        with pytest.raises(ValueError, match="only 1 responsibility|only.*responsibilities"):
            agent._validate_output(doc)

    def test_sanitize_output(self):
        agent = ArchitectAgent(llm_service=None)
        doc = ArchitectureDoc(
            title="  Test Architecture  ",
            overview="  Sanitization test overview that is long enough to be valid after trimming.  ",
            architecture_pattern="  microservices  ",
            components=[
                ComponentSpec(
                    name="  API Gateway  ",
                    description="  Gateway with extra spaces around the description text  ",
                    technology="  FastAPI 0.111  ",
                    responsibilities=["  Route requests  ", "  Auth users  "],
                    dependencies=["  Database  "],
                    api_endpoints=[{"  path  ": "  /api/v1/login  ", "  method  ": "  POST  "}],
                ),
                ComponentSpec(
                    name="  Order Service  ",
                    description="  Order processing with spacing around descriptive text here  ",
                    technology="  Python 3.12  ",
                    responsibilities=["  Process orders  ", "  Validate orders  "],
                    dependencies=["  API Gateway  "],
                ),
                ComponentSpec(
                    name="  Notification Service  ",
                    description="  Send notifications with proper spacing cleanup required  ",
                    technology="  Celery 5.4  ",
                    responsibilities=["  Send emails  ", "  Send push  "],
                    dependencies=["  Order Service  "],
                ),
            ],
            data_flow=[
                {"step": "  1  ", "description": "  Request to gateway  "},
                {"step": "  2  ", "description": "  Gateway to order service  "},
                {"step": "  3  ", "description": "  Order processing  "},
                {"step": "  4  ", "description": "  Notification sent  "},
            ],
            tech_stack={
                "  language  ": "  Python 3.12  ",
                "  framework  ": "  FastAPI 0.111  ",
                "  database  ": "  PostgreSQL 16  ",
                "  cache  ": "  Redis 7.2  ",
                "  message_queue  ": "  RabbitMQ 3.13  ",
            },
            deployment_strategy="  Docker deployment with Kubernetes orchestration for production scaling.  ",
            security_considerations=[
                "  JWT authentication  ",
                "  TLS encryption  ",
                "  Rate limiting  ",
            ],
        )
        sanitized = agent._sanitize_output(doc)
        assert sanitized.title == "Test Architecture"
        assert sanitized.components[0].name == "API Gateway"
        assert sanitized.components[0].technology == "FastAPI 0.111"
        assert sanitized.components[0].responsibilities[0] == "Route requests"
        assert sanitized.tech_stack["language"] == "Python 3.12"
        assert sanitized.security_considerations[0] == "JWT authentication"
        assert sanitized.data_flow[0]["step"] == "1"

    def test_build_state_updates(self, sample_idea: str):
        agent = ArchitectAgent(llm_service=None)
        state = create_initial_state(idea=sample_idea)
        output = ArchitectureDoc(
            title="Test",
            overview="Test architecture overview with enough length to pass validation checks here.",
            architecture_pattern="Layered",
            components=[
                ComponentSpec(
                    name="API",
                    description="API gateway for all incoming request routing and handling.",
                    technology="FastAPI 0.111",
                    responsibilities=["Route requests", "Auth users"],
                    dependencies=[],
                ),
                ComponentSpec(
                    name="Service",
                    description="Core business logic service for application processing workflows.",
                    technology="Python 3.12",
                    responsibilities=["Business logic", "Data processing"],
                    dependencies=["API"],
                ),
                ComponentSpec(
                    name="DB",
                    description="Database service for persistent data storage and management.",
                    technology="PostgreSQL 16",
                    responsibilities=["Store data", "Query data"],
                    dependencies=[],
                ),
            ],
            data_flow=[
                {"step": "1", "description": "Request to API"},
                {"step": "2", "description": "API to Service"},
                {"step": "3", "description": "Service to DB"},
                {"step": "4", "description": "Response back"},
            ],
            tech_stack={
                "language": "Python 3.12",
                "framework": "FastAPI 0.111",
                "database": "PostgreSQL 16",
                "cache": "Redis 7.2",
                "message_queue": "RabbitMQ 3.13",
            },
            deployment_strategy="Docker Compose for dev, Kubernetes for prod with HPA and rolling updates.",
            security_considerations=[
                "JWT auth",
                "TLS encryption",
                "Rate limiting",
            ],
        )
        token_usage = {"prompt_tokens": 150, "completion_tokens": 300, "total_tokens": 450}
        updates = agent._build_state_updates(state, output, token_usage)
        assert "architecture" in updates
        assert updates["current_agent"] == "architect"
        assert updates["revision"] == 1
        assert "token_usage" in updates
        assert updates["token_usage"][0]["total_tokens"] == 450

    def test_agent_has_retries(self):
        agent = ArchitectAgent(llm_service=None)
        assert agent.max_retries == 2
