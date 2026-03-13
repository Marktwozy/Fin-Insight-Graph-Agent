# Daily Batch Operations Runbook

## Objective
Publish one consistent daily batch covering documents, market data, graph projections, and evaluation artifacts.

## Steps
1. Load documents into Postgres and persist canonical chunks.
2. Load market bars and move the batch state from `staged` to `validated`.
3. Index document chunks into Qdrant.
4. Project entities and events into Neo4j.
5. Mark the batch as `published` only after all stores are aligned.
6. Run `research_smoke` and `event_smoke` suites to validate the published batch.

## Failure handling
- If document ingestion fails, keep the batch in `failed` and do not publish retrieval indexes.
- If Qdrant or Neo4j lags behind Postgres, roll forward with a repaired batch rather than mutating the published batch in place.
- If evaluation faithfulness regresses, pause promotion and inspect the trace, retrieval evidence, and reflection report for the failing run.