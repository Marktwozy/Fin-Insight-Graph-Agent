# Pipeline Smoke Audit Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist pipeline-smoke runs so the end-to-end flow has a durable audit trail instead of only terminal output.

**Architecture:** Add a dedicated `pipeline_smoke_runs` table plus repository, then inject that repository into `PipelineSmokeRunner` so each run writes an initial `running` row and completes it with batch status, research/event payloads, duration, and failure context. Keep the worker CLI surface unchanged apart from richer, now-audited behavior.

**Tech Stack:** SQLAlchemy, Alembic, existing worker CLI, FastAPI TestClient, Pytest, Ruff, MyPy

---

## Chunk 1: Storage And Runner Wiring

### Task 1: Add failing tests first

**Files:**
- Create: `D:/myAgent/.worktrees/fin-insight-v1/tests/integration/storage/test_pipeline_smoke_run_repository.py`
- Modify: `D:/myAgent/.worktrees/fin-insight-v1/tests/unit/apps/test_pipeline_smoke.py`
- Modify: `D:/myAgent/.worktrees/fin-insight-v1/tests/integration/storage/test_initial_schema.py`

- [ ] **Step 1: Write the failing repository and runner audit tests**
- [ ] **Step 2: Run tests to verify they fail because the model/repository do not exist yet**
- [ ] **Step 3: Implement the minimal model, repository, migration, and runner wiring**
- [ ] **Step 4: Run the tests again and confirm they pass**

## Chunk 2: Docs And Verification

### Task 2: Document and verify the audited flow

**Files:**
- Modify: `D:/myAgent/.worktrees/fin-insight-v1/README.md`
- Modify: `D:/myAgent/.worktrees/fin-insight-v1/docs/runbooks/daily-batch-ops.md`

- [ ] **Step 1: Document `pipeline_smoke_runs` in README and runbook**
- [ ] **Step 2: Run focused verification for pipeline-smoke, storage schema, lint, and typing**
- [ ] **Step 3: Commit and push**