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
- Multi-company source sync: `uv run python -m apps.worker.main --job source-sync-batch --targets-file examples/source_sync_targets.example.json --batch-id batch-20260313`
- Daily orchestrated batch: `uv run python -m apps.worker.main --job daily-batch --targets-file examples/source_sync_targets.example.json`
- Daily orchestrated batch without publish: `uv run python -m apps.worker.main --job daily-batch --targets-file examples/source_sync_targets.example.json --skip-publish`
- Batch publish: `uv run python -m apps.worker.main --job publish-batch --batch-id batch-20260313`
- Standalone graph gate: `uv run python -m apps.evaluator.main --suite graph_retrieval_smoke --dataset-root tests/fixtures/evaluation --enforce-thresholds`

## Scheduling pattern
- `daily-batch` is the entrypoint intended for Windows Task Scheduler or cron.
- If `--batch-id` is omitted, the worker generates the batch id from the local date as `batch-YYYYMMDD`.
- You can override the date with `--batch-date YYYY-MM-DD` for replay or backfill.
- Recommended scheduler target on Windows:
  `uv run python -m apps.worker.main --job daily-batch --targets-file examples/source_sync_targets.example.json`

## Reliability notes
- Source sync is idempotent for the same `batch_id`: rerunning the same company or daily batch rewrites the same canonical documents and chunk IDs instead of duplicating rows.
- News ingestion deduplicates repeated articles by URL, and `source-sync-batch` also deduplicates repeated cross-ticker articles within the same batch.
- Source sync retries transient upstream failures according to `FIGA_SOURCE_SYNC_MAX_ATTEMPTS` and `FIGA_SOURCE_SYNC_RETRY_BACKOFF_SECONDS`.
- If retries are exhausted, the batch is marked `failed` so the run can be repaired and replayed explicitly.
- Validated or published batches are protected from in-place resync to preserve reproducibility.

## Query checks after sync
- Research sample:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/query `
  -ContentType 'application/json' `
  -Body '{"question":"What supply risks does NVIDIA face?","batch_id":"batch-20260313"}'
```

- Event sample:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/query `
  -ContentType 'application/json' `
  -Body '{"event_input":"A packaging bottleneck hits TSMC CoWoS capacity","batch_id":"batch-20260313"}'
```

## Failure handling
- If document ingestion fails, keep the batch in `failed` and do not publish retrieval indexes.
- If the graph quality gate fails, move the batch to `failed_quality_gate`, inspect the latest gate audit row, and repopulate missing graph evidence before retrying validation.
- If Qdrant or Neo4j lags behind Postgres, roll forward with a repaired batch rather than mutating the published batch in place.
- If evaluation faithfulness regresses, pause promotion and inspect the trace, retrieval evidence, and reflection report for the failing run.