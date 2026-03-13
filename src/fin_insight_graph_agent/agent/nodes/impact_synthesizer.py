from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fin_insight_graph_agent.common.models import EvidenceBundle


def synthesize_impact(
    state: Mapping[str, Any],
    response_generator: Any | None = None,
) -> dict[str, Any]:
    evidence: list[EvidenceBundle] = state.get('evidence', [])
    citations = [bundle.citation_payload for bundle in evidence]
    if response_generator is not None:
        final_response = response_generator.generate_event_answer(
            event_input=state.get('event_input', ''),
            evidence_texts=[bundle.content for bundle in evidence],
        )
    elif evidence:
        lead = evidence[0].content.strip()
        prefix = 'Based on the retrieved evidence, this event may affect downstream exposure.'
        final_response = f'{prefix} {lead}'
    else:
        final_response = 'No grounded evidence found for this event yet.'
    return {
        'citations': citations,
        'draft_response': final_response,
        'final_response': final_response,
    }