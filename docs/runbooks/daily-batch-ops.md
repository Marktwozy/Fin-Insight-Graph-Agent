# Daily Batch Operations Runbook

## Objective
Publish one consistent daily batch covering documents, market data, graph projections, and evaluation artifacts.

## Steps
1. Run source sync and keep the new batch in `staged`.
2. Index document chunks into Qdrant.
3. Project entities and events into Neo4j.
4. Run `research_smoke` and `event_smoke` suites to validate the batch.
5. Run the graph quality gate before promotion.
6. Mark the batch as `validated` only if the graph gate passes.
7. Mark the batch as `published` only after all stores are aligned and the graph gate is green.

## Worker commands
- Source sync: `uv run python -m apps.worker.main --job source-sync --ticker NVDA --cik 1045810 --batch-id batch-20260313`
- Batch publish: `uv run python -m apps.worker.main --job publish-batch --batch-id batch-20260313`
- Standalone graph gate: `uv run python -m apps.evaluator.main --suite graph_retrieval_smoke --dataset-root tests/fixtures/evaluation --enforce-thresholds`

## Failure handling
- If document ingestion fails, keep the batch in `failed` and do not publish retrieval indexes.
- If the graph quality gate fails, move the batch to `failed_quality_gate`, inspect the latest gate audit row, and repopulate missing graph evidence before retrying validation.
- If Qdrant or Neo4j lags behind Postgres, roll forward with a repaired batch rather than mutating the published batch in place.
- If evaluation faithfulness regresses, pause promotion and inspect the trace, retrieval evidence, and reflection report for the failing run.