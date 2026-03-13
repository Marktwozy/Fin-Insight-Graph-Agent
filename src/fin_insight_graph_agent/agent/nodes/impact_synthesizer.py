from __future__ import annotations

from fin_insight_graph_agent.common.models import EvidenceBundle


def synthesize_impact(state: dict) -> dict:
    evidence: list[EvidenceBundle] = state.get("evidence", [])
    citations = [bundle.citation_payload for bundle in evidence]
    if evidence:
        lead = evidence[0].content.strip()
        prefix = "Based on the retrieved evidence, this event may affect downstream exposure."
        final_response = f"{prefix} {lead}"
    else:
        final_response = "No grounded evidence found for this event yet."
    return {
        "citations": citations,
        "draft_response": final_response,
        "final_response": final_response,
    }