# Local Development Runbook

## Prerequisites
- Python 3.12+
- `uv`
- Docker Desktop

## Boot the stack
1. Run `docker compose up -d postgres qdrant neo4j prometheus grafana`.
2. Run `uv run alembic upgrade head`.
3. Run `uv run uvicorn apps.api.main:create_app --factory --reload`.

## Core checks
- API health: `http://127.0.0.1:8000/health`
- Metrics: `http://127.0.0.1:8000/metrics`
- Grafana: `http://127.0.0.1:3000`
- Qdrant: `http://127.0.0.1:6333`
- Neo4j Browser: `http://127.0.0.1:7474`

## Test commands
- Unit and integration: `uv run pytest tests/unit tests/integration -v`
- Evaluation: `uv run pytest tests/evaluation -v`
- Lint: `uv run ruff check .`
- Types: `uv run mypy src`