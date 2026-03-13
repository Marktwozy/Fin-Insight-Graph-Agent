# Fin-Insight-Graph-Agent

Engineering foundation for a financial intelligence agent built on LangGraph, Postgres, Qdrant, and Neo4j.

## V1 scope
- Research question answering over filings, news, and market context
- Event-driven impact analysis with bounded reflection
- Structured short-term memory and compression
- OpenTelemetry and Prometheus instrumentation with Grafana dashboards
- Evaluation harness with RAGAS-style metrics and business metrics

## Core architecture
- `Postgres`: canonical store for documents, chunks, market data, agent runs, memory, and evaluation results
- `Qdrant`: hybrid text retrieval plane
- `Neo4j`: entity and event relationship retrieval plane
- `LangGraph`: research and event analysis workflows

## Local development
1. Start the stack with `docker compose up -d postgres qdrant neo4j prometheus grafana`.
2. Apply schema changes with `uv run alembic upgrade head`.
3. Start the API with `uv run uvicorn apps.api.main:create_app --factory --reload`.
4. Run the evaluator with `uv run python -m apps.evaluator.main --suite research_smoke --dataset-root tests/fixtures/evaluation`.

## Verification
- `uv run pytest tests/unit tests/integration tests/evaluation -v`
- `uv run ruff check .`
- `uv run mypy src`

## Documentation
- `docs/guides/v1-implementation-walkthrough.md`
- `docs/runbooks/local-dev.md`
- `docs/runbooks/daily-batch-ops.md`
- `docs/adr/0001-postgres-qdrant-neo4j.md`