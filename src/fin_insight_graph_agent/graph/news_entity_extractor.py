from __future__ import annotations

import re
from hashlib import sha1

from fin_insight_graph_agent.graph.project_entities import GraphProjectionRecord
from fin_insight_graph_agent.ingestion.connectors.alpha_vantage import (
    NewsSentimentArticle,
)

_TOPIC_RULES = (
    ("advanced_packaging", ("packaging", "capacity", "bottleneck")),
    ("supply_chain", ("supplier", "supply", "lead time")),
    ("ai_demand", ("ai", "datacenter", "gpu")),
)


def extract_graph_projection_records(
    articles: list[NewsSentimentArticle],
    *,
    ticker: str,
    batch_id: str,
) -> list[GraphProjectionRecord]:
    entity_id = f"company:{ticker.lower()}"
    entity_name = ticker.upper()
    records: list[GraphProjectionRecord] = []
    for article in articles:
        topic = _infer_topic(article)
        records.append(
            GraphProjectionRecord(
                entity_id=entity_id,
                entity_name=entity_name,
                entity_type="Company",
                batch_id=batch_id,
                related_event_id=_build_event_id(article.title),
                related_event_name=article.title,
                related_topic=topic,
                ticker=ticker.upper(),
            )
        )
    return records


def _infer_topic(article: NewsSentimentArticle) -> str:
    haystack = f"{article.title} {article.summary}".lower()
    for topic, keywords in _TOPIC_RULES:
        if any(keyword in haystack for keyword in keywords):
            return topic
    return "market_news"


def _build_event_id(title: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    if not normalized:
        normalized = sha1(title.encode()).hexdigest()[:12]
    return f"event:{normalized}"