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

    records = extract_graph_projection_records(
        [article],
        ticker="NVDA",
        batch_id="batch-20260313",
    )

    assert records[0].entity_id == "company:nvda"
    assert records[0].entity_name == "NVDA"
    assert records[0].related_topic == "advanced_packaging"
    assert records[0].related_event_id.startswith("event:capacity_tightening")


def test_extract_graph_projection_records_emits_multiple_entities_and_event_classification():
    article = NewsSentimentArticle(
        title="TSMC maintenance and U.S. export controls may pressure NVIDIA and AMD supply",
        url="https://example.com/news/chip-supply",
        time_published="20260313T150000",
        summary=(
            "TSMC fab maintenance and tighter export restrictions may hit NVIDIA and AMD "
            "GPU supply chains."
        ),
        source="Reuters",
    )

    records = extract_graph_projection_records(
        [article],
        ticker="NVDA",
        batch_id="batch-20260313",
    )

    entity_ids = {record.entity_id for record in records}
    topics = {record.related_topic for record in records}
    event_ids = {record.related_event_id for record in records}

    assert {"company:nvda", "company:amd", "company:tsmc"}.issubset(entity_ids)
    assert "export_controls" in topics
    assert any(event_id.startswith("event:export_control") for event_id in event_ids)