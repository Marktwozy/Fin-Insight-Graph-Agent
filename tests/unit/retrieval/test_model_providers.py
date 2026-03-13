from fin_insight_graph_agent.agent.response_generator import (
    OpenAICompatibleChatClient,
    OpenAICompatibleResponseGenerator,
)
from fin_insight_graph_agent.retrieval.embeddings import OpenAICompatibleDenseEmbedder
from fin_insight_graph_agent.retrieval.reranker import (
    DashScopeTextRerankerClient,
    HttpBGERerankerClient,
)


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


def test_http_bge_reranker_client_maps_indexed_results_back_to_input_order():
    transport = FakeTransport(
        {
            'results': [
                {'index': 1, 'score': 0.93},
                {'index': 0, 'score': 0.34},
            ]
        }
    )
    client = HttpBGERerankerClient(
        base_url='https://reranker.example/v1/rerank',
        model='bge-reranker-v2-m3',
        api_key='secret',
        transport=transport,
    )

    scores = client.score('GPU demand', ['doc-a', 'doc-b'])

    assert scores == [0.34, 0.93]


def test_dashscope_reranker_client_uses_text_rerank_endpoint_for_gte_models():
    transport = FakeTransport(
        {
            'output': {
                'results': [
                    {'index': 1, 'relevance_score': 0.88},
                    {'index': 0, 'relevance_score': 0.21},
                ]
            }
        }
    )
    client = DashScopeTextRerankerClient(
        base_url='https://dashscope.aliyuncs.com',
        model='gte-rerank-v2',
        api_key='secret',
        transport=transport,
    )

    scores = client.score('GPU demand', ['doc-a', 'doc-b'])

    assert scores == [0.21, 0.88]
    assert transport.calls[0]['url'].endswith('/api/v1/services/rerank/text-rerank/text-rerank')
    assert transport.calls[0]['payload']['input']['query'] == 'GPU demand'
    assert transport.calls[0]['headers']['Authorization'] == 'Bearer secret'


def test_dashscope_reranker_client_uses_qwen_compatible_endpoint_when_requested():
    transport = FakeTransport(
        {
            'results': [
                {'index': 0, 'relevance_score': 0.66},
                {'index': 1, 'relevance_score': 0.12},
            ]
        }
    )
    client = DashScopeTextRerankerClient(
        base_url='https://dashscope.aliyuncs.com',
        model='qwen3-rerank-8b',
        api_key='secret',
        instruct='Rank financial evidence by relevance.',
        transport=transport,
    )

    scores = client.score('GPU demand', ['doc-a', 'doc-b'])

    assert scores == [0.66, 0.12]
    assert transport.calls[0]['url'].endswith('/compatible-api/v1/reranks')
    assert transport.calls[0]['payload']['instruct'] == 'Rank financial evidence by relevance.'
    assert transport.calls[0]['payload']['top_n'] == 2


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