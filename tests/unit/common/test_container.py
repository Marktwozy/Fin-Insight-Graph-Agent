from fin_insight_graph_agent.common.container import build_container
from fin_insight_graph_agent.common.settings import AppSettings


def test_build_container_wires_runtime_dependencies(monkeypatch):
    captured = {}
    qdrant_client = object()
    neo4j_client = object()
    engine = object()
    text_retriever = ('text', qdrant_client)
    graph_retriever = ('graph', neo4j_client)
    market_retriever = ('market', engine)

    monkeypatch.setattr(
        'fin_insight_graph_agent.common.container.build_qdrant_client',
        lambda *args, **kwargs: qdrant_client,
    )
    monkeypatch.setattr(
        'fin_insight_graph_agent.common.container.build_neo4j_client',
        lambda *args, **kwargs: neo4j_client,
    )
    monkeypatch.setattr(
        'fin_insight_graph_agent.common.container.create_db_engine',
        lambda *args, **kwargs: engine,
    )
    monkeypatch.setattr(
        'fin_insight_graph_agent.common.container.build_dense_embedder',
        lambda settings: 'dense',
    )
    monkeypatch.setattr(
        'fin_insight_graph_agent.common.container.build_reranker',
        lambda settings: 'reranker',
    )
    monkeypatch.setattr(
        'fin_insight_graph_agent.common.container.build_response_generator',
        lambda settings: 'llm',
    )
    monkeypatch.setattr(
        'fin_insight_graph_agent.common.container.TextRetriever',
        lambda client: text_retriever,
    )
    monkeypatch.setattr(
        'fin_insight_graph_agent.common.container.GraphRetriever',
        lambda client: graph_retriever,
    )
    monkeypatch.setattr(
        'fin_insight_graph_agent.common.container.MarketContextRetriever',
        lambda current_engine: market_retriever,
    )
    monkeypatch.setattr('fin_insight_graph_agent.common.container.EvidenceMerger', lambda: 'merger')
    monkeypatch.setattr(
        'fin_insight_graph_agent.common.container.build_research_graph',
        lambda deps: captured.setdefault('research', deps) or deps,
    )
    monkeypatch.setattr(
        'fin_insight_graph_agent.common.container.build_event_graph',
        lambda deps: captured.setdefault('event', deps) or deps,
    )

    build_container(AppSettings())

    assert captured['research'].response_generator == 'llm'
    assert captured['research'].reranker == 'reranker'
    assert captured['research'].text_retriever == text_retriever
    assert captured['research'].graph_retriever == graph_retriever
    assert captured['research'].market_retriever == market_retriever