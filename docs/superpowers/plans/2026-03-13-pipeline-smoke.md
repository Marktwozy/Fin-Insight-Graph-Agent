# Pipeline Smoke Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repeatable end-to-end smoke path that runs the daily batch flow and exercises both research and event query routes in-process.

**Architecture:** Add a focused worker-side `pipeline_smoke` runner that composes the existing `daily-batch` orchestrator with an in-process FastAPI `TestClient` against `/v1/query`. Wire a new worker job for this path, keep defaults for one research and one event prompt, and return a compact summary that is easy to run manually or automate later.

**Tech Stack:** Python, FastAPI `TestClient`, existing worker CLI, LangGraph container wiring, Pytest, Ruff, MyPy

---

## Chunk 1: Runner And Worker Wiring

### Task 1: Add pipeline smoke tests first

**Files:**
- Create: `D:/myAgent/.worktrees/fin-insight-v1/tests/unit/apps/test_pipeline_smoke.py`
- Modify: `D:/myAgent/.worktrees/fin-insight-v1/tests/unit/apps/test_worker_main.py`

- [ ] **Step 1: Write the failing runner test**

```python
def test_pipeline_smoke_runs_daily_batch_and_both_query_routes():
    summary = runner.run(...)
    assert summary.batch_status == "published"
    assert summary.research.status == "passed"
    assert summary.event.status == "passed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/apps/test_pipeline_smoke.py tests/unit/apps/test_worker_main.py -q`
Expected: FAIL because the runner and worker job do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```python
class PipelineSmokeRunner:
    def run(...):
        batch_summary = orchestrator.run(...)
        ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/apps/test_pipeline_smoke.py tests/unit/apps/test_worker_main.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/apps/test_pipeline_smoke.py tests/unit/apps/test_worker_main.py apps/worker/pipeline_smoke.py apps/worker/main.py
git commit -m "feat: add pipeline smoke runner"
```

## Chunk 2: Verification And Docs

### Task 2: Add operator docs and verify the flow

**Files:**
- Modify: `D:/myAgent/.worktrees/fin-insight-v1/README.md`
- Modify: `D:/myAgent/.worktrees/fin-insight-v1/docs/runbooks/daily-batch-ops.md`

- [ ] **Step 1: Document the new worker job**

```md
- Pipeline smoke: `uv run python -m apps.worker.main --job pipeline-smoke --targets-file ...`
```

- [ ] **Step 2: Run focused verification**

Run: `uv run pytest tests/unit/apps/test_pipeline_smoke.py tests/unit/apps/test_worker_main.py tests/integration/api/test_query_endpoint.py tests/integration/test_research_e2e.py tests/integration/test_event_e2e.py -q`
Expected: PASS

- [ ] **Step 3: Run repository quality checks**

Run: `uv run ruff check apps src tests`
Expected: PASS

Run: `uv run mypy src apps/worker/main.py apps/worker/pipeline_smoke.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add README.md docs/runbooks/daily-batch-ops.md
git commit -m "docs: add pipeline smoke runbook"
```