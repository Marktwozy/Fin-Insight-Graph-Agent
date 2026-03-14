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

## Model runtime configuration
- `FIGA_EMBEDDING_PROVIDER=simple|openai_compatible`
- `FIGA_LLM_PROVIDER=heuristic|openai_compatible`
- `FIGA_RERANKER_PROVIDER=heuristic|http_bge|dashscope`
- `FIGA_MODEL_API_BASE_URL` and `FIGA_MODEL_API_KEY` configure OpenAI-compatible embedding and chat endpoints
- `FIGA_RERANKER_API_URL`, `FIGA_RERANKER_API_KEY`, and `FIGA_RERANKER_MODEL` configure remote reranker endpoints
- `FIGA_RERANKER_INSTRUCT` optionally sets a custom instruction for `qwen3-rerank` models
- `FIGA_SOURCE_SYNC_MAX_ATTEMPTS` and `FIGA_SOURCE_SYNC_RETRY_BACKOFF_SECONDS` configure source-sync retry behavior
- `FIGA_PROMPT_VERSION` is persisted with evaluation runs
- `FIGA_QDRANT_COLLECTION_NAME` selects the target collection for source-sync indexing

## Local development
1. Start the stack with `docker compose up -d postgres qdrant neo4j prometheus grafana`.
2. Apply schema changes with `uv run alembic upgrade head`.
3. Start the API with `uv run uvicorn apps.api.main:create_app --factory --reload`.
4. Run the evaluator with `uv run python -m apps.evaluator.main --suite research_smoke --dataset-root tests/fixtures/evaluation`.
5. Gate graph retrieval quality with `uv run python -m apps.evaluator.main --suite graph_retrieval_smoke --dataset-root tests/fixtures/evaluation --enforce-thresholds`.
6. Run an official source sync with `uv run python -m apps.worker.main --job source-sync --ticker NVDA --cik 1045810 --batch-id batch-20260313`.
7. Run a multi-company source sync with `uv run python -m apps.worker.main --job source-sync-batch --targets-file examples/source_sync_targets.example.json --batch-id batch-20260313`.
8. Run the daily orchestrated job with `uv run python -m apps.worker.main --job daily-batch --targets-file examples/source_sync_targets.example.json`.
9. Run the full in-process pipeline smoke with `uv run python -m apps.worker.main --job pipeline-smoke --targets-file examples/source_sync_targets.example.json --batch-id batch-20260313`.
10. Promote a batch manually with `uv run python -m apps.worker.main --job publish-batch --batch-id batch-20260313`.

## Query a research sample locally
1. Prepare `.env.local` with your embedding, reranker, and LLM provider settings.
2. Sync a batch with `source-sync`, `source-sync-batch`, `daily-batch`, or `pipeline-smoke`.
3. Start the API with `uv run uvicorn apps.api.main:create_app --factory --reload`.
4. Call the research route from PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/query `
  -ContentType 'application/json' `
  -Body '{"question":"What supply risks does NVIDIA face?","batch_id":"batch-20260313"}'
```

5. Call the event route from PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/query `
  -ContentType 'application/json' `
  -Body '{"event_input":"A packaging bottleneck hits TSMC CoWoS capacity","batch_id":"batch-20260313"}'
```

## Verification
- `uv run pytest tests/unit tests/integration tests/evaluation -v`
- `uv run ruff check .`
- `uv run mypy src`

## Batch audit and observability
- Daily orchestrated runs persist into the `daily_batch_runs` table with terminal status, tickers, validation payload, duration, and error context.
- Pipeline smoke runs persist into the `pipeline_smoke_runs` table with batch status, research/event smoke payloads, duration, and failure context.
- Graph publish gates persist into `batch_quality_gate_runs` for batch-level promotion audit.
- Prometheus exposes `figa_daily_batch_run_total`, `figa_daily_batch_run_seconds`, and `figa_source_sync_retry_total` for scheduler health and retry visibility.

## Documentation
- `docs/reports/v1-technical-brief.md`
- `docs/guides/v1-implementation-walkthrough.md`
- `docs/runbooks/local-dev.md`
- `docs/runbooks/daily-batch-ops.md`
- `docs/adr/0001-postgres-qdrant-neo4j.md`