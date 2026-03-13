# Fin-Insight-Graph-Agent V1 Technical Brief

## 1. Project Positioning
Fin-Insight-Graph-Agent is an engineering-oriented financial intelligence agent for multi-source information fusion, research question answering, and event-driven impact analysis. The project is designed for financial analysts and active investors who need to track filings, market data, policy changes, and sudden events, then quickly trace affected companies and evidence chains.

The V1 objective is not to maximize scenario breadth immediately. Instead, it establishes a robust engineering foundation so later capabilities such as enterprise graph expansion, supply-chain propagation, and richer event monitoring can be added without re-architecting the system.

## 2. Problem Statement
Traditional investment research workflows are fragmented. Analysts read large volumes of reports, filings, and news manually, then separately check market data and relationship context. When a black-swan event occurs, the difficult step is not only finding the event itself, but mapping the impact path from event to company, from company to position, and from raw evidence to explainable conclusion.

Three engineering gaps motivated this project:
- heterogeneous sources are not normalized into one evidence model
- long-context reasoning is expensive and brittle without structured memory and compression
- agent quality is hard to trust without observability, traceability, and repeatable evaluation

## 3. V1 Scope
The current V1 includes:
- dual workflows: research Q&A and event-driven impact analysis
- canonical data plane on Postgres
- hybrid retrieval on Qdrant
- graph expansion on Neo4j
- structured memory with compression and replay
- bounded reflection for safer grounded responses
- OpenTelemetry, Prometheus, and Grafana observability hooks
- evaluation harness with RAGAS-style metric names and custom business metrics
- API, worker, and evaluator entrypoints

## 4. Architecture Decision
### 4.1 Storage split
The system adopts a three-plane architecture:
- Postgres: source of truth for documents, chunks, market bars, batches, memory, agent runs, and evaluation runs
- Qdrant: hybrid retrieval execution plane for dense and sparse text retrieval
- Neo4j: relationship expansion plane for entities, events, and topics

This architecture balances engineering simplicity and future graph reasoning extensibility better than a single-store prototype.

### 4.2 Agent design
The agent layer is implemented with LangGraph and exposes two primary flows:
- research graph: rewrite, decompose, retrieve, rerank, grounded answer
- event graph: normalize, retrieve, synthesize impact, reflect, revise once

Both flows share the same retrieval and evidence contracts, which keeps downstream logic stable.

### 4.3 Memory design
Instead of treating memory as free-form conversation recall, V1 uses structured memory snapshots containing confirmed facts, open hypotheses, evidence pointers, pending questions, and confidence notes. This is important for financial analysis because facts and hypotheses must remain clearly separated for auditability.

## 5. Key Engineering Outcomes
### 5.1 Unified evidence contract
All retrieval branches converge into `EvidenceBundle`, which prevents graph nodes and generators from depending directly on heterogeneous storage clients.

### 5.2 Batch-based publication
Daily batch publication controls ensure retrieval and analysis happen against a stable published snapshot, which is important for reproducibility and evaluation.

### 5.3 Quality loop from day one
Observability and evaluation were built as first-class modules rather than postponed. This makes it possible to inspect request traces, monitor latency and cost, and run smoke evaluation suites continuously.

## 6. Real Data Source Integration Stage
The project has now entered the first real-source integration slice. The current implementation adds official adapters for:
- SEC EDGAR on `data.sec.gov`
  - submission history endpoint
  - company facts endpoint
  - compliant `User-Agent` header handling
- Alpha Vantage
  - daily adjusted market bars via CSV API

This is a deliberate first step. It brings the project from purely local fixture ingestion toward production-shaped connectors while still keeping the integration surface small and testable.

## 7. Current Deliverables
The repository now contains:
- infrastructure and developer workflow setup
- database schema and migrations
- document and market ingestion pipelines
- hybrid retrieval and graph retrieval adapters
- memory and compression logic
- dual LangGraph workflows
- API, worker, evaluator entrypoints
- observability and evaluation modules
- E2E, unit, integration, and evaluation tests
- ADRs, runbooks, walkthrough docs, and this technical brief

## 8. Verification Status
At the time of this brief, the project has been freshly verified with:
- full unit, integration, and evaluation test suite
- Ruff linting
- MyPy type checking

This means the repository is not only functionally implemented but also in a releasable engineering state for continued V1.1 work.

## 9. Next Steps
Recommended next-stage priorities are:
- add a source orchestration layer for scheduled SEC and market sync jobs
- connect a real news source adapter and normalize event/news documents into the canonical ingestion path
- replace heuristic evaluation adapters with production RAGAS experiment configuration
- expand graph projection toward enterprise relationships and supply-chain edges
- add model-backed embeddings and reranker configuration for production use

## 10. Summary
V1 successfully establishes an engineering-grade base for a financial intelligence agent. The most important result is not a single demo flow, but a coherent architecture that unifies canonical storage, retrieval, graph reasoning, structured memory, observability, and evaluation. This foundation makes the system suitable for iterative expansion toward a more capable investment research and enterprise graph analysis platform.