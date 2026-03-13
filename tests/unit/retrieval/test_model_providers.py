from fin_insight_graph_agent.agent.response_generator import (
    OpenAICompatibleChatClient,
    OpenAICompatibleResponseGenerator,
)
from fin_insight_graph_agent.retrieval.embeddings import OpenAICompatibleDenseEmbedder
from fin_insight_graph_agent.retrieval.reranker import HttpBGERerankerClient


class FakeTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post_json(self, url, *, payload, headers=None):
        self.calls.append({'url': url, 'payload': payload, 'headers': headers or {}})
        return self.response


def test_openai_compatible_dense_embedder_calls_embeddings_endpoint_and_parses_vector():
    transport = FakeTransport({'data': [{'embedding': [0.1, 0.2, 0.3]}]})
    embedder = OpenAICompatibleDenseEmbedder(
        base_url='https://models.example/v1',
        model='text-embedding-3-small',
        dimensions=3,
        api_key='secret',
        transport=transport,
    )

    vector = embedder.encode('NVIDIA supply chain')

    assert vector == [0.1, 0.2, 0.3]
    assert transport.calls[0]['url'] == 'https://models.example/v1/embeddings'
    assert transport.calls[0]['payload']['model'] == 'text-embedding-3-small'
    assert transport.calls[0]['headers']['Authorization'] == 'Bearer secret'


def test_http_bge_reranker_client_calls_remote_endpoint_and_returns_scores():
    transport = FakeTransport({'scores': [0.8, 0.3]})
    client = HttpBGERerankerClient(
        base_url='https://reranker.example/v1/rerank',
        model='bge-reranker-v2-m3',
        api_key='secret',
        transport=transport,
    )

    scores = client.score('GPU demand', ['NVIDIA demand is rising', 'Oil prices fell'])

    assert scores == [0.8, 0.3]
    assert transport.calls[0]['payload']['documents'] == [
        'NVIDIA demand is rising',
        'Oil prices fell',
    ]


def test_openai_compatible_response_generator_calls_chat_completion_endpoint():
    transport = FakeTransport(
        {'choices': [{'message': {'content': 'Grounded answer about NVIDIA suppliers.'}}]}
    )
    client = OpenAICompatibleChatClient(
        base_url='https://models.example/v1',
        model='gpt-4.1-mini',
        api_key='secret',
        transport=transport,
    )
    generator = OpenAICompatibleResponseGenerator(
        client=client,
        prompt_version='prompt:v2',
    )

    answer = generator.generate_research_answer(
        question='What are NVIDIA supply risks?',
        evidence_texts=['TSMC maintenance may pressure packaging supply.'],
    )

    assert answer == 'Grounded answer about NVIDIA suppliers.'
    assert transport.calls[0]['url'] == 'https://models.example/v1/chat/completions'
    assert transport.calls[0]['payload']['model'] == 'gpt-4.1-mini'