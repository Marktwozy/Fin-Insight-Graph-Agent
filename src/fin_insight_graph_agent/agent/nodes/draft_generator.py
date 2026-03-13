from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fin_insight_graph_agent.common.models import EvidenceBundle


def generate_draft(
    state: Mapping[str, Any],
    response_generator: Any | None = None,
) -> dict[str, Any]:
    evidence: list[EvidenceBundle] = state.get('evidence', [])
    citations = [bundle.citation_payload for bundle in evidence]
    if response_generator is not None:
        final_response = response_generator.generate_research_answer(
            question=state.get('question', ''),
            evidence_texts=[bundle.content for bundle in evidence],
        )
    elif evidence:
        final_response = ' '.join(bundle.content for bundle in evidence[:2])
    else:
        final_response = 'No grounded evidence found.'
    return {'citations': citations, 'final_response': final_response}