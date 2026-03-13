from fin_insight_graph_agent.graph.news_entity_extractor import extract_graph_projection_records
from fin_insight_graph_agent.ingestion.connectors.alpha_vantage import NewsSentimentArticle


def test_extract_graph_projection_records_maps_news_article_to_company_event_and_topic():
    article = NewsSentimentArticle(
        title="NVIDIA supplier capacity tightens after packaging bottleneck",
        url="https://example.com/news/nvda-supply",
        time_published="20260313T120000",
        summary="Advanced packaging capacity remains tight for NVIDIA suppliers.",
        source="Reuters",
    )

    records = extract_graph_projection_records([article], ticker="NVDA", batch_id="batch-20260313")

    assert records[0].entity_id == "company:nvda"
    assert records[0].entity_name == "NVDA"
    assert records[0].related_topic == "advanced_packaging"
    assert records[0].related_event_id.startswith("event:")