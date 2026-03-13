from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from fin_insight_graph_agent.agent.nodes.draft_generator import generate_draft
from fin_insight_graph_agent.agent.nodes.query_rewriter import rewrite_query
from fin_insight_graph_agent.agent.nodes.question_decomposer import decompose_question
from fin_insight_graph_agent.agent.nodes.router import route_request
from fin_insight_graph_agent.common.models import EvidenceBundle


class ResearchGraphState(TypedDict, total=False):
    question: str
    batch_id: str
    route: str
    rewritten_question: str
    subquestions: list[str]
    evidence: list[EvidenceBundle]
    citations: list[dict[str, str]]
    final_response: str


def _extract_market_refs(question: str) -> list[str]:
    upper_words = [
        word.strip("?,.")
        for word in question.split()
        if word.isupper() and 1 < len(word) <= 5
    ]
    return upper_words


def build_research_graph(dependencies: Any):
    workflow = StateGraph(ResearchGraphState)

    def retrieve_evidence(state: ResearchGraphState) -> dict:
        question = state.get("rewritten_question") or state.get("question", "")
        batch_id = state.get("batch_id", "")
        text_results = dependencies.text_retriever.search(question, batch_id=batch_id)
        graph_results = dependencies.graph_retriever.expand_entities([], batch_id=batch_id)
        market_results = dependencies.market_retriever.search(
            _extract_market_refs(question),
            batch_id=batch_id,
        )
        merged = dependencies.evidence_merger.merge(
            [text_results, graph_results, market_results]
        )
        ranked = dependencies.reranker.rank(question, merged)
        return {"evidence": ranked}

    workflow.add_node("router", route_request)
    workflow.add_node("query_rewriter", rewrite_query)
    workflow.add_node("question_decomposer", decompose_question)
    workflow.add_node("retrieve_evidence", retrieve_evidence)
    workflow.add_node("draft_generator", generate_draft)

    workflow.set_entry_point("router")
    workflow.add_edge("router", "query_rewriter")
    workflow.add_edge("query_rewriter", "question_decomposer")
    workflow.add_edge("question_decomposer", "retrieve_evidence")
    workflow.add_edge("retrieve_evidence", "draft_generator")
    workflow.add_edge("draft_generator", END)

    return workflow.compile()