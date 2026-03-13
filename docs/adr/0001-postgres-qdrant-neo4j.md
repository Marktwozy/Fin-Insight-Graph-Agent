# ADR 0001: Postgres + Qdrant + Neo4j for the V1 data plane

## Status
Accepted

## Context
Fin-Insight-Graph-Agent needs one canonical system of record, one retrieval-optimized store, and one relationship-oriented store. The platform must support research question answering, event-driven impact analysis, structured memory, replayable evaluation, and a future expansion toward enterprise graph reasoning.

## Decision
Use Postgres as the canonical store for documents, chunks, market data, agent runs, memory snapshots, and evaluation results. Use Qdrant as the hybrid retrieval plane for dense and sparse text search. Use Neo4j as the graph plane for entity and event neighborhood expansion.

## Consequences
This split keeps transactional truth in Postgres, retrieval execution in Qdrant, and relationship traversal in Neo4j. The tradeoff is higher operational complexity than a single-store prototype, but it preserves a clean path to GraphRAG, reflection auditing, and evaluation replay without replatforming.