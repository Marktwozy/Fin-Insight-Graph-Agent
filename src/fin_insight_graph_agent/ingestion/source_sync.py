from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from fin_insight_graph_agent.common.settings import AppSettings
from fin_insight_graph_agent.graph.neo4j_client import build_neo4j_client
from fin_insight_graph_agent.graph.news_entity_extractor import (
    extract_graph_projection_records,
)
from fin_insight_graph_agent.graph.project_entities import EntityProjector
from fin_insight_graph_agent.ingestion.chunker import chunk_document
from fin_insight_graph_agent.ingestion.connectors.alpha_vantage import (
    AlphaVantageClient,
    NewsSentimentArticle,
)
from fin_insight_graph_agent.ingestion.connectors.sec_edgar import SecEdgarClient
from fin_insight_graph_agent.ingestion.document_loader import RawDocument
from fin_insight_graph_agent.ingestion.document_normalizer import normalize_document
from fin_insight_graph_agent.ingestion.document_repository import DocumentRepository
from fin_insight_graph_agent.storage.db import create_db_engine
from fin_insight_graph_agent.storage.repositories.batch_repository import BatchRepository
from fin_insight_graph_agent.storage.repositories.market_repository import MarketRepository


@dataclass(slots=True)
class SourceSyncSummary:
    batch_id: str
    ticker: str
    document_count: int
    market_bar_count: int
    news_document_count: int


class OfficialSourceSyncJob:
    def __init__(
        self,
        sec_client: SecEdgarClient | Any,
        alpha_vantage_client: AlphaVantageClient | Any,
        document_repository: DocumentRepository | Any,
        market_repository: MarketRepository | Any,
        batch_repository: BatchRepository | Any,
        entity_projector: EntityProjector | Any | None = None,
        chunk_size: int = 900,
        overlap: int = 120,
    ) -> None:
        self._sec_client = sec_client
        self._alpha_vantage_client = alpha_vantage_client
        self._document_repository = document_repository
        self._market_repository = market_repository
        self._batch_repository = batch_repository
        self._entity_projector = entity_projector
        self._chunk_size = chunk_size
        self._overlap = overlap

    def sync_company(self, cik: str, ticker: str, batch_id: str) -> SourceSyncSummary:
        self._batch_repository.create_batch(batch_id, "staged")

        submissions = self._sec_client.fetch_submissions(cik)
        company_facts = self._sec_client.fetch_company_facts(cik)
        news_feed = self._alpha_vantage_client.fetch_news_sentiment([ticker], limit=20)
        documents = [
            self._build_raw_document(
                source_uri=f"sec://submissions/{cik}",
                source_type="sec.submissions",
                ticker=ticker,
                title=f"{ticker} submissions",
                payload=submissions,
            ),
            self._build_raw_document(
                source_uri=f"sec://companyfacts/{cik}",
                source_type="sec.companyfacts",
                ticker=ticker,
                title=f"{ticker} company facts",
                payload=company_facts,
            ),
            *[
                self._build_news_document(article=article, ticker=ticker)
                for article in news_feed
            ],
        ]

        for raw_document in documents:
            normalized_document = normalize_document(raw_document, batch_id=batch_id)
            chunks = chunk_document(
                normalized_document,
                chunk_size=self._chunk_size,
                overlap=self._overlap,
            )
            self._document_repository.save_document_with_chunks(normalized_document, chunks)

        if self._entity_projector is not None and news_feed:
            self._entity_projector.project(
                extract_graph_projection_records(
                    news_feed,
                    ticker=ticker,
                    batch_id=batch_id,
                )
            )

        bars = self._alpha_vantage_client.fetch_daily_adjusted(ticker)
        self._market_repository.upsert_daily_bars(bars, batch_id=batch_id)

        return SourceSyncSummary(
            batch_id=batch_id,
            ticker=ticker,
            document_count=len(documents),
            market_bar_count=len(bars),
            news_document_count=len(news_feed),
        )

    @staticmethod
    def _build_raw_document(
        *,
        source_uri: str,
        source_type: str,
        ticker: str,
        title: str,
        payload: dict[str, Any],
    ) -> RawDocument:
        return RawDocument(
            source_uri=source_uri,
            source_type=source_type,
            ticker=ticker,
            title=title,
            text=json.dumps(payload, indent=2, sort_keys=True),
        )

    @staticmethod
    def _build_news_document(article: NewsSentimentArticle | Any, ticker: str) -> RawDocument:
        return RawDocument(
            source_uri=article.url,
            source_type="news.alpha_vantage",
            ticker=ticker,
            title=article.title,
            text=json.dumps(
                {
                    "title": article.title,
                    "summary": article.summary,
                    "source": article.source,
                    "time_published": article.time_published,
                    "url": article.url,
                },
                indent=2,
                sort_keys=True,
            ),
        )


def build_official_source_sync_job(settings: AppSettings | None = None) -> OfficialSourceSyncJob:
    resolved_settings = settings or AppSettings()
    engine = create_db_engine()
    return OfficialSourceSyncJob(
        sec_client=SecEdgarClient(
            base_url=resolved_settings.sec_api_base_url,
            user_agent=resolved_settings.sec_api_user_agent,
        ),
        alpha_vantage_client=AlphaVantageClient(
            base_url=resolved_settings.alpha_vantage_base_url,
            api_key=resolved_settings.alpha_vantage_api_key,
        ),
        document_repository=DocumentRepository(engine),
        market_repository=MarketRepository(engine),
        batch_repository=BatchRepository(engine),
        entity_projector=EntityProjector(build_neo4j_client()),
    )