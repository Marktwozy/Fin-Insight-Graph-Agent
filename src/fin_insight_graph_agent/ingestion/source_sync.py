from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from time import sleep
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
from fin_insight_graph_agent.retrieval.index_chunks import (
    ChunkIndexRecord,
    QdrantChunkIndexer,
    build_chunk_indexer,
)
from fin_insight_graph_agent.storage.db import create_db_engine
from fin_insight_graph_agent.storage.repositories.batch_repository import BatchRepository
from fin_insight_graph_agent.storage.repositories.market_repository import MarketRepository


@dataclass(slots=True)
class CompanySyncTarget:
    ticker: str
    cik: str


@dataclass(slots=True)
class SourceSyncSummary:
    batch_id: str
    ticker: str
    document_count: int
    market_bar_count: int
    news_document_count: int
    indexed_chunk_count: int = 0


@dataclass(slots=True)
class SourceSyncBatchSummary:
    batch_id: str
    company_count: int
    tickers: list[str]
    document_count: int
    market_bar_count: int
    news_document_count: int
    indexed_chunk_count: int


class OfficialSourceSyncJob:
    def __init__(
        self,
        sec_client: SecEdgarClient | Any,
        alpha_vantage_client: AlphaVantageClient | Any,
        document_repository: DocumentRepository | Any,
        market_repository: MarketRepository | Any,
        batch_repository: BatchRepository | Any,
        entity_projector: EntityProjector | Any | None = None,
        chunk_indexer: QdrantChunkIndexer | Any | None = None,
        qdrant_collection_name: str = 'chunks',
        chunk_size: int = 900,
        overlap: int = 120,
        max_attempts: int = 3,
        retry_backoff_seconds: float = 0.0,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self._sec_client = sec_client
        self._alpha_vantage_client = alpha_vantage_client
        self._document_repository = document_repository
        self._market_repository = market_repository
        self._batch_repository = batch_repository
        self._entity_projector = entity_projector
        self._chunk_indexer = chunk_indexer
        self._qdrant_collection_name = qdrant_collection_name
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._max_attempts = max_attempts
        self._retry_backoff_seconds = retry_backoff_seconds
        self._sleeper = sleeper or sleep

    def sync_company(self, cik: str, ticker: str, batch_id: str) -> SourceSyncSummary:
        self._batch_repository.ensure_staged_batch(batch_id)
        try:
            return self._sync_company_internal(
                cik=cik,
                ticker=ticker,
                batch_id=batch_id,
            )
        except Exception:
            self._batch_repository.update_status(batch_id, 'failed')
            raise

    def sync_companies(
        self,
        targets: list[CompanySyncTarget],
        batch_id: str,
    ) -> SourceSyncBatchSummary:
        if not targets:
            raise ValueError('At least one sync target is required')

        self._batch_repository.ensure_staged_batch(batch_id)
        seen_news_keys: set[str] = set()
        try:
            summaries = [
                self._sync_company_internal(
                    cik=target.cik,
                    ticker=target.ticker,
                    batch_id=batch_id,
                    seen_news_keys=seen_news_keys,
                )
                for target in targets
            ]
        except Exception:
            self._batch_repository.update_status(batch_id, 'failed')
            raise
        return SourceSyncBatchSummary(
            batch_id=batch_id,
            company_count=len(summaries),
            tickers=[summary.ticker for summary in summaries],
            document_count=sum(summary.document_count for summary in summaries),
            market_bar_count=sum(summary.market_bar_count for summary in summaries),
            news_document_count=sum(summary.news_document_count for summary in summaries),
            indexed_chunk_count=sum(summary.indexed_chunk_count for summary in summaries),
        )

    def _sync_company_internal(
        self,
        *,
        cik: str,
        ticker: str,
        batch_id: str,
        seen_news_keys: set[str] | None = None,
    ) -> SourceSyncSummary:
        submissions = self._call_with_retry(
            lambda: self._sec_client.fetch_submissions(cik),
            operation_name=f'{ticker}.sec_submissions',
        )
        company_facts = self._call_with_retry(
            lambda: self._sec_client.fetch_company_facts(cik),
            operation_name=f'{ticker}.sec_company_facts',
        )
        fetched_news_feed = self._call_with_retry(
            lambda: self._alpha_vantage_client.fetch_news_sentiment([ticker], limit=20),
            operation_name=f'{ticker}.news_sentiment',
        )
        news_feed = _deduplicate_news_articles(
            fetched_news_feed,
            seen_keys=seen_news_keys,
        )
        documents = [
            self._build_raw_document(
                source_uri=f'sec://submissions/{cik}',
                source_type='sec.submissions',
                ticker=ticker,
                title=f'{ticker} submissions',
                payload=submissions,
            ),
            self._build_raw_document(
                source_uri=f'sec://companyfacts/{cik}',
                source_type='sec.companyfacts',
                ticker=ticker,
                title=f'{ticker} company facts',
                payload=company_facts,
            ),
            *[
                self._build_news_document(article=article, ticker=ticker)
                for article in news_feed
            ],
        ]

        chunk_index_records: list[ChunkIndexRecord] = []
        for raw_document in documents:
            normalized_document = normalize_document(raw_document, batch_id=batch_id)
            chunks = chunk_document(
                normalized_document,
                chunk_size=self._chunk_size,
                overlap=self._overlap,
            )
            self._document_repository.save_document_with_chunks(normalized_document, chunks)
            chunk_index_records.extend(
                self._build_chunk_index_records(normalized_document, chunks)
            )

        if self._chunk_indexer is not None and chunk_index_records:
            self._chunk_indexer.ensure_collection(self._qdrant_collection_name)
            self._chunk_indexer.index(self._qdrant_collection_name, chunk_index_records)

        if self._entity_projector is not None and news_feed:
            self._entity_projector.project(
                extract_graph_projection_records(
                    news_feed,
                    ticker=ticker,
                    batch_id=batch_id,
                )
            )

        bars = self._call_with_retry(
            lambda: self._alpha_vantage_client.fetch_daily_adjusted(ticker),
            operation_name=f'{ticker}.daily_adjusted',
        )
        self._market_repository.upsert_daily_bars(bars, batch_id=batch_id)

        return SourceSyncSummary(
            batch_id=batch_id,
            ticker=ticker,
            document_count=len(documents),
            market_bar_count=len(bars),
            news_document_count=len(news_feed),
            indexed_chunk_count=len(chunk_index_records),
        )

    def _call_with_retry(
        self,
        operation: Callable[[], Any],
        *,
        operation_name: str,
    ) -> Any:
        last_error: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                return operation()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self._max_attempts:
                    break
                delay_seconds = self._retry_backoff_seconds * attempt
                if delay_seconds > 0:
                    self._sleeper(delay_seconds)
        assert last_error is not None
        raise RuntimeError(
            f'Source sync operation failed after {self._max_attempts} attempts: '
            f'{operation_name}'
        ) from last_error

    @staticmethod
    def _build_chunk_index_records(normalized_document, chunks) -> list[ChunkIndexRecord]:
        ticker = normalized_document.ticker_tags[0] if normalized_document.ticker_tags else ''
        entity_refs = [f'company:{tag.lower()}' for tag in normalized_document.ticker_tags]
        market_refs = [f'ticker:{tag}' for tag in normalized_document.ticker_tags]
        return [
            ChunkIndexRecord(
                chunk_id=chunk.chunk_id,
                doc_id=normalized_document.document_id,
                content=chunk.chunk_text,
                source_type=normalized_document.source_type,
                ticker=ticker,
                publish_date=normalized_document.publication_date,
                batch_id=normalized_document.batch_id,
                entity_refs=entity_refs,
                time_refs=[normalized_document.publication_date],
                market_refs=market_refs,
            )
            for chunk in chunks
        ]

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
            source_type='news.alpha_vantage',
            ticker=ticker,
            title=article.title,
            text=json.dumps(
                {
                    'title': article.title,
                    'summary': article.summary,
                    'source': article.source,
                    'time_published': article.time_published,
                    'url': article.url,
                },
                indent=2,
                sort_keys=True,
            ),
        )


def _deduplicate_news_articles(
    articles: list[NewsSentimentArticle | Any],
    *,
    seen_keys: set[str] | None = None,
) -> list[NewsSentimentArticle | Any]:
    deduplicated: list[NewsSentimentArticle | Any] = []
    local_keys: set[str] = set()
    global_keys = seen_keys if seen_keys is not None else set()
    for article in articles:
        article_key = _news_article_key(article)
        if article_key in local_keys or article_key in global_keys:
            continue
        local_keys.add(article_key)
        global_keys.add(article_key)
        deduplicated.append(article)
    return deduplicated


def _news_article_key(article: NewsSentimentArticle | Any) -> str:
    url = str(getattr(article, 'url', '') or '').strip().lower()
    title = str(getattr(article, 'title', '') or '').strip().lower()
    published = str(getattr(article, 'time_published', '') or '').strip().lower()
    if url:
        return url
    return f'{title}|{published}'


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
        chunk_indexer=build_chunk_indexer(resolved_settings),
        qdrant_collection_name=resolved_settings.qdrant_collection_name,
        max_attempts=resolved_settings.source_sync_max_attempts,
        retry_backoff_seconds=resolved_settings.source_sync_retry_backoff_seconds,
    )