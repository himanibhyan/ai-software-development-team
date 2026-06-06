# AI Software Development Team

A multi-agent AI system that simulates a complete software development team. Given a software idea, the system autonomously generates requirements, architecture, source code, tests, and documentation.

## Architecture

Six specialized AI agents collaborate via a LangGraph pipeline:

1. **Requirements Agent** - Produces structured PRD/SRS documents
2. **Architect Agent** - Designs system architecture with component specs
3. **Developer Agent** - Generates complete, working source code
4. **Tester Agent** - Creates unit and integration test suites
5. **Code Review Agent** - Reviews code quality and suggests improvements
6. **Documentation Agent** - Generates README, API docs, and setup guides

## Quick Start

```bash
# Clone and start infrastructure
make dev-up

# Install dependencies
make dev

# Run migrations
make migrate

# Start the API
cd backend && uvicorn app.main:app --reload
```

## Tech Stack

- **Backend**: Python 3.12, FastAPI, LangGraph, SQLAlchemy
- **Database**: PostgreSQL 16, ChromaDB (vectors)
- **Queue**: Redis + Celery
- **Frontend**: React + Next.js
- **Infrastructure**: Docker Compose, Prometheus, Grafana

## Documentation

Detailed documentation is available in `docs/`:

- [SRS](docs/SRS.md) - Software Requirements Specification
- [Architecture](docs/ARCHITECTURE.md) - System Architecture Design
- [Folder Structure](docs/FOLDER_STRUCTURE.md) - Project Tree
- [Roadmap](docs/ROADMAP.md) - Development Plan

## License

MIT
