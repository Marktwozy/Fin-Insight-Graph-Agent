from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fin_insight_graph_agent.agent.graphs.event import build_event_graph
from fin_insight_graph_agent.agent.graphs.research import build_research_graph
from fin_insight_graph_agent.agent.response_generator import build_response_generator
from fin_insight_graph_agent.common.settings import AppSettings
from fin_insight_graph_agent.graph.graph_retriever import GraphRetriever
from fin_insight_graph_agent.graph.neo4j_client import build_neo4j_client
from fin_insight_graph_agent.retrieval.embeddings import build_dense_embedder
from fin_insight_graph_agent.retrieval.evidence_merger import EvidenceMerger
from fin_insight_graph_agent.retrieval.market_context_retriever import MarketContextRetriever
from fin_insight_graph_agent.retrieval.qdrant_client import build_qdrant_client
from fin_insight_graph_agent.retrieval.reranker import build_reranker
from fin_insight_graph_agent.retrieval.sparse_encoder import SimpleSparseEncoder
from fin_insight_graph_agent.retrieval.text_retriever import TextRetriever
from fin_insight_graph_agent.storage.db import create_db_engine


@dataclass(slots=True)
class GraphDependencies:
    text_retriever: Any
    graph_retriever: Any
    market_retriever: Any
    evidence_merger: Any
    reranker: Any
    response_generator: Any


@dataclass(slots=True)
class ApplicationContainer:
    research_graph: Any
    event_graph: Any


def build_container(settings: AppSettings | None = None) -> ApplicationContainer:
    resolved_settings = settings or AppSettings()
    engine = create_db_engine()
    dense_embedder = build_dense_embedder(resolved_settings)
    qdrant_client = build_qdrant_client(
        dense_embedder=dense_embedder,
        sparse_encoder=SimpleSparseEncoder(),
    )
    dependencies = GraphDependencies(
        text_retriever=TextRetriever(qdrant_client),
        graph_retriever=GraphRetriever(build_neo4j_client()),
        market_retriever=MarketContextRetriever(engine),
        evidence_merger=EvidenceMerger(),
        reranker=build_reranker(resolved_settings),
        response_generator=build_response_generator(resolved_settings),
    )
    return ApplicationContainer(
        research_graph=build_research_graph(dependencies),
        event_graph=build_event_graph(dependencies),
    )