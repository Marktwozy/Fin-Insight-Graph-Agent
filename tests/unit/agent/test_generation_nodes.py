from fin_insight_graph_agent.agent.nodes.draft_generator import generate_draft
from fin_insight_graph_agent.agent.nodes.impact_synthesizer import synthesize_impact
from fin_insight_graph_agent.common.models import EvidenceBundle


class FakeResponseGenerator:
    prompt_version = 'prompt:v2'
    model_version = 'openai-compatible:gpt-4.1-mini'

    def generate_research_answer(self, *, question, evidence_texts):
        return f'research::{question}::{len(evidence_texts)}'

    def generate_event_answer(self, *, event_input, evidence_texts):
        return f'event::{event_input}::{len(evidence_texts)}'


def test_generate_draft_uses_response_generator_when_present():
    result = generate_draft(
        {
            'question': 'What are NVIDIA supply risks?',
            'evidence': [_bundle('TSMC maintenance may pressure packaging supply.')],
        },
        response_generator=FakeResponseGenerator(),
    )

    assert result['final_response'] == 'research::What are NVIDIA supply risks?::1'


def test_synthesize_impact_uses_response_generator_when_present():
    result = synthesize_impact(
        {
            'event_input': 'TSMC maintenance',
            'evidence': [_bundle('TSMC maintenance may pressure packaging supply.')],
        },
        response_generator=FakeResponseGenerator(),
    )

    assert result['final_response'] == 'event::TSMC maintenance::1'
    assert result['draft_response'] == 'event::TSMC maintenance::1'


def _bundle(content):
    return EvidenceBundle(
        evidence_id='chunk-1',
        source_type='news',
        content=content,
        score_raw=0.9,
        score_reranked=None,
        entity_refs=['company:nvda'],
        time_refs=['2026-03-13'],
        market_refs=['ticker:NVDA'],
        citation_payload={'doc_id': 'doc-1', 'chunk_id': 'chunk-1'},
        batch_id='batch-20260313',
        retrieval_path='qdrant.hybrid',
    )