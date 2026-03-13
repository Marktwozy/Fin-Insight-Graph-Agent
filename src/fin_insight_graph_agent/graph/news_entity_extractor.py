from __future__ import annotations

import re
from hashlib import sha1

from fin_insight_graph_agent.graph.project_entities import GraphProjectionRecord
from fin_insight_graph_agent.ingestion.connectors.alpha_vantage import NewsSentimentArticle

_COMPANY_ALIASES: dict[str, tuple[str, tuple[str, ...]]] = {
    "NVDA": ("company:nvda", ("nvidia", "nvda")),
    "AMD": ("company:amd", ("amd", "advanced micro devices")),
    "TSMC": ("company:tsmc", ("tsmc", "taiwan semiconductor")),
    "INTC": ("company:intc", ("intel", "intc")),
    "ASML": ("company:asml", ("asml",)),
    "AVGO": ("company:avgo", ("broadcom", "avgo")),
    "SSNLF": ("company:ssnlf", ("samsung", "samsung electronics")),
}

_EVENT_RULES = (
    ("export_control", ("export control", "export controls", "export restriction", "sanction")),
    ("fab_maintenance", ("fab maintenance", "maintenance", "shutdown", "outage")),
    ("labor_disruption", ("strike", "walkout", "labor action", "union")),
    ("capacity_tightening", ("capacity", "bottleneck", "tightens", "tight supply", "lead time")),
    ("ai_demand", ("ai demand", "gpu demand", "datacenter demand")),
)

_TOPIC_RULES = (
    ("export_controls", ("export control", "export controls", "export restriction", "sanction")),
    ("advanced_packaging", ("packaging", "advanced packaging", "capacity", "bottleneck")),
    ("supply_chain", ("supplier", "supply", "lead time", "procurement")),
    ("fab_operations", ("fab", "foundry", "maintenance", "wafer")),
    ("ai_demand", ("ai", "datacenter", "gpu")),
    ("labor_disruption", ("strike", "walkout", "labor")),
)


def extract_graph_projection_records(
    articles: list[NewsSentimentArticle],
    *,
    ticker: str,
    batch_id: str,
) -> list[GraphProjectionRecord]:
    records: list[GraphProjectionRecord] = []
    fallback_ticker = ticker.upper()

    for article in articles:
        event_type = _infer_event_type(article)
        topic = _infer_topic(article)
        matched_tickers = _extract_tickers(article)
        if fallback_ticker not in matched_tickers:
            matched_tickers.append(fallback_ticker)

        event_id = _build_event_id(article.title, event_type)
        for matched_ticker in matched_tickers:
            entity_id, _ = _COMPANY_ALIASES.get(
                matched_ticker,
                (f"company:{matched_ticker.lower()}", (matched_ticker.lower(),)),
            )
            records.append(
                GraphProjectionRecord(
                    entity_id=entity_id,
                    entity_name=matched_ticker,
                    entity_type="Company",
                    batch_id=batch_id,
                    related_event_id=event_id,
                    related_event_name=article.title,
                    related_topic=topic,
                    ticker=matched_ticker,
                )
            )
    return records


def _extract_tickers(article: NewsSentimentArticle) -> list[str]:
    haystack = f"{article.title} {article.summary}".lower()
    matched: list[str] = []
    for ticker, (_, aliases) in _COMPANY_ALIASES.items():
        if any(alias in haystack for alias in aliases):
            matched.append(ticker)
    return matched


def _infer_topic(article: NewsSentimentArticle) -> str:
    haystack = f"{article.title} {article.summary}".lower()
    for topic, keywords in _TOPIC_RULES:
        if any(keyword in haystack for keyword in keywords):
            return topic
    return "market_news"


def _infer_event_type(article: NewsSentimentArticle) -> str:
    haystack = f"{article.title} {article.summary}".lower()
    for event_type, keywords in _EVENT_RULES:
        if any(keyword in haystack for keyword in keywords):
            return event_type
    return "market_signal"


def _build_event_id(title: str, event_type: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    if not normalized:
        normalized = sha1(title.encode()).hexdigest()[:12]
    return f"event:{event_type}:{normalized}"