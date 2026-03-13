from __future__ import annotations

from fin_insight_graph_agent.common.models import EvidenceBundle


def generate_draft(state: dict) -> dict:
    evidence: list[EvidenceBundle] = state.get("evidence", [])
    citations = [bundle.citation_payload for bundle in evidence]
    if evidence:
        final_response = " ".join(bundle.content for bundle in evidence[:2])
    else:
        final_response = "No grounded evidence found."
    return {"citations": citations, "final_response": final_response}