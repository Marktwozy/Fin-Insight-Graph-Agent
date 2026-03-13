from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from fin_insight_graph_agent.agent.nodes.event_normalizer import normalize_event
from fin_insight_graph_agent.agent.nodes.impact_synthesizer import synthesize_impact
from fin_insight_graph_agent.agent.nodes.reflection_checker import ReflectionChecker
from fin_insight_graph_agent.agent.nodes.revision_gate import apply_revision
from fin_insight_graph_agent.common.models import EvidenceBundle


class EventGraphState(TypedDict, total=False):
    event_input: str
    batch_id: str
    normalized_event: str
    subquestions: list[str]
    evidence: list[EvidenceBundle]
    citations: list[dict[str, str]]
    draft_response: str
    final_response: str
    reflection_report: object


def _extract_market_refs(text: str) -> list[str]:
    upper_words = [
        word.strip('?,.')
        for word in text.split()
        if word.isupper() and 1 < len(word) <= 5
    ]
    return upper_words


def build_event_graph(dependencies: Any) -> Any:
    workflow = StateGraph(EventGraphState)
    checker = ReflectionChecker()

    def retrieve_evidence(state: EventGraphState) -> dict[str, Any]:
        event_text = state.get('normalized_event') or state.get('event_input', '')
        batch_id = state.get('batch_id', '')
        text_results = dependencies.text_retriever.search(event_text, batch_id=batch_id)
        graph_results = dependencies.graph_retriever.expand_entities([], batch_id=batch_id)
        market_results = dependencies.market_retriever.search(
            _extract_market_refs(event_text),
            batch_id=batch_id,
        )
        merged = dependencies.evidence_merger.merge(
            [text_results, graph_results, market_results]
        )
        ranked = dependencies.reranker.rank(event_text, merged)
        return {'evidence': ranked}

    def draft_impact(state: EventGraphState) -> dict[str, Any]:
        return synthesize_impact(
            state,
            response_generator=getattr(dependencies, 'response_generator', None),
        )

    def reflect(state: EventGraphState) -> dict[str, Any]:
        evidence = state.get('evidence', [])
        report = checker.check(
            draft_text=state.get('draft_response', ''),
            evidence_texts=[bundle.content for bundle in evidence],
        )
        return {'reflection_report': report}

    workflow.add_node(
        'event_normalizer',
        normalize_event,
    )  # type: ignore[call-overload,type-var]
    workflow.add_node('retrieve_evidence', retrieve_evidence)  # type: ignore[arg-type,type-var]
    workflow.add_node('impact_synthesizer', draft_impact)  # type: ignore[arg-type,type-var]
    workflow.add_node('reflection_checker', reflect)  # type: ignore[arg-type,type-var]
    workflow.add_node(
        'revision_gate',
        apply_revision,
    )  # type: ignore[call-overload,type-var]

    workflow.set_entry_point('event_normalizer')
    workflow.add_edge('event_normalizer', 'retrieve_evidence')
    workflow.add_edge('retrieve_evidence', 'impact_synthesizer')
    workflow.add_edge('impact_synthesizer', 'reflection_checker')
    workflow.add_edge('reflection_checker', 'revision_gate')
    workflow.add_edge('revision_gate', END)

    return workflow.compile()