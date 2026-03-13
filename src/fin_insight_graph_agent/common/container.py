from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fin_insight_graph_agent.agent.graphs.event import build_event_graph
from fin_insight_graph_agent.agent.graphs.research import build_research_graph


class NullRetriever:
    def search(self, *args: Any, **kwargs: Any) -> list:
        return []

    def expand_entities(self, *args: Any, **kwargs: Any) -> list:
        return []


class NullEvidenceMerger:
    def merge(self, evidence_lists: list[list]) -> list:
        merged: list = []
        for evidence_list in evidence_lists:
            merged.extend(evidence_list)
        return merged


class NullReranker:
    def rank(self, query: str, bundles: list) -> list:
        return bundles


@dataclass(slots=True)
class GraphDependencies:
    text_retriever: Any
    graph_retriever: Any
    market_retriever: Any
    evidence_merger: Any
    reranker: Any


@dataclass(slots=True)
class ApplicationContainer:
    research_graph: Any
    event_graph: Any


def build_container() -> ApplicationContainer:
    dependencies = GraphDependencies(
        text_retriever=NullRetriever(),
        graph_retriever=NullRetriever(),
        market_retriever=NullRetriever(),
        evidence_merger=NullEvidenceMerger(),
        reranker=NullReranker(),
    )
    return ApplicationContainer(
        research_graph=build_research_graph(dependencies),
        event_graph=build_event_graph(dependencies),
    )