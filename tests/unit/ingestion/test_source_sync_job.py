from datetime import date
from decimal import Decimal

import pytest

from fin_insight_graph_agent.ingestion.market_loader import DailyBarRecord
from fin_insight_graph_agent.ingestion.source_sync import (
    CompanySyncTarget,
    OfficialSourceSyncJob,
)


class FakeSecClient:
    def fetch_submissions(self, cik):
        return {"cik": cik, "form": ["10-K"]}

    def fetch_company_facts(self, cik):
        return {"cik": cik, "facts": {"Revenue": "mock"}}


class FlakySecClient(FakeSecClient):
    def __init__(self, failures_before_success=1):
        self.failures_before_success = failures_before_success
        self.submission_calls = 0

    def fetch_submissions(self, cik):
        self.submission_calls += 1
        if self.submission_calls <= self.failures_before_success:
            raise RuntimeError('temporary sec outage')
        return super().fetch_submissions(cik)


class AlwaysFailingSecClient(FakeSecClient):
    def fetch_submissions(self, cik):
        raise RuntimeError('persistent sec outage')


class FakeNewsArticle:
    def __init__(self, title, url, summary):
        self.title = title
        self.url = url
        self.summary = summary
        self.source = "Reuters"
        self.time_published = "20260313T120000"


class FakeAlphaVantageClient:
    def fetch_daily_adjusted(self, symbol, outputsize="compact"):
        return [
            DailyBarRecord(
                ticker=symbol,
                trade_date=date(2026, 3, 13),
                open_price=Decimal("118.00"),
                high_price=Decimal("120.00"),
                low_price=Decimal("117.50"),
                close_price=Decimal("119.50"),
                volume=1200000,
            )
        ]

    def fetch_news_sentiment(self, tickers, limit=20):
        symbol = tickers[0]
        return [
            FakeNewsArticle(
                title=f"{symbol} supplier capacity tightens",
                url=f"https://example.com/news/{symbol.lower()}-supply",
                summary="Capacity remains tight across packaging suppliers.",
            )
        ]


class FakeDocumentRepository:
    def __init__(self):
        self.saved = []

    def save_document_with_chunks(self, document, chunks):
        self.saved.append((document, chunks))


class FakeMarketRepository:
    def __init__(self):
        self.saved = []

    def upsert_daily_bars(self, bars, batch_id):
        self.saved.append((bars, batch_id))


class FakeBatchRepository:
    def __init__(self):
        self.created = []
        self.updated = []
        self.batches = {}

    def create_batch(self, batch_id, status):
        self.created.append((batch_id, status))
        self.batches[batch_id] = status
        return {"batch_id": batch_id, "status": status}

    def ensure_staged_batch(self, batch_id):
        self.created.append((batch_id, 'staged'))
        self.batches[batch_id] = 'staged'
        return {"batch_id": batch_id, "status": 'staged'}

    def update_status(self, batch_id, status):
        self.updated.append((batch_id, status))
        self.batches[batch_id] = status
        return {"batch_id": batch_id, "status": status}


class FakeEntityProjector:
    def __init__(self):
        self.projected = []

    def project(self, records):
        self.projected.extend(records)


class FakeChunkIndexer:
    def __init__(self):
        self.ensured = []
        self.indexed = []

    def ensure_collection(self, collection_name):
        self.ensured.append(collection_name)

    def index(self, collection_name, records):
        self.indexed.append((collection_name, records))


def test_official_source_sync_job_persists_sec_documents_market_bars_news_and_graph_projection():
    document_repository = FakeDocumentRepository()
    market_repository = FakeMarketRepository()
    batch_repository = FakeBatchRepository()
    entity_projector = FakeEntityProjector()
    chunk_indexer = FakeChunkIndexer()
    job = OfficialSourceSyncJob(
        sec_client=FakeSecClient(),
        alpha_vantage_client=FakeAlphaVantageClient(),
        document_repository=document_repository,
        market_repository=market_repository,
        batch_repository=batch_repository,
        entity_projector=entity_projector,
        chunk_indexer=chunk_indexer,
    )

    summary = job.sync_company(cik="1045810", ticker="NVDA", batch_id="batch-20260313")

    assert batch_repository.created == [("batch-20260313", "staged")]
    assert len(document_repository.saved) == 3
    assert market_repository.saved[0][1] == "batch-20260313"
    assert summary.document_count == 3
    assert summary.market_bar_count == 1
    assert summary.news_document_count == 1
    assert summary.indexed_chunk_count > 0
    assert chunk_indexer.ensured == ["chunks"]
    assert chunk_indexer.indexed[0][0] == "chunks"
    assert entity_projector.projected[0].entity_id == "company:nvda"
    assert entity_projector.projected[0].related_event_name == "NVDA supplier capacity tightens"


def test_official_source_sync_job_syncs_multiple_companies_into_one_batch():
    document_repository = FakeDocumentRepository()
    market_repository = FakeMarketRepository()
    batch_repository = FakeBatchRepository()
    entity_projector = FakeEntityProjector()
    chunk_indexer = FakeChunkIndexer()
    job = OfficialSourceSyncJob(
        sec_client=FakeSecClient(),
        alpha_vantage_client=FakeAlphaVantageClient(),
        document_repository=document_repository,
        market_repository=market_repository,
        batch_repository=batch_repository,
        entity_projector=entity_projector,
        chunk_indexer=chunk_indexer,
    )

    summary = job.sync_companies(
        targets=[
            CompanySyncTarget(ticker="NVDA", cik="1045810"),
            CompanySyncTarget(ticker="AMD", cik="2488"),
        ],
        batch_id="batch-20260314",
    )

    assert batch_repository.created == [("batch-20260314", "staged")]
    assert summary.company_count == 2
    assert summary.tickers == ["NVDA", "AMD"]
    assert summary.document_count == 6
    assert summary.market_bar_count == 2
    assert summary.news_document_count == 2
    assert summary.indexed_chunk_count > 0
    assert len(document_repository.saved) == 6
    assert len(market_repository.saved) == 2
    assert len(chunk_indexer.indexed) == 2


def test_official_source_sync_job_retries_transient_source_failures():
    document_repository = FakeDocumentRepository()
    market_repository = FakeMarketRepository()
    batch_repository = FakeBatchRepository()
    sleeper_calls = []
    sec_client = FlakySecClient(failures_before_success=1)
    job = OfficialSourceSyncJob(
        sec_client=sec_client,
        alpha_vantage_client=FakeAlphaVantageClient(),
        document_repository=document_repository,
        market_repository=market_repository,
        batch_repository=batch_repository,
        max_attempts=3,
        retry_backoff_seconds=0.25,
        sleeper=sleeper_calls.append,
    )

    summary = job.sync_company(cik="1045810", ticker="NVDA", batch_id="batch-20260315")

    assert summary.document_count == 3
    assert sec_client.submission_calls == 2
    assert sleeper_calls == [0.25]
    assert batch_repository.updated == []


def test_official_source_sync_job_marks_batch_failed_when_retries_are_exhausted():
    batch_repository = FakeBatchRepository()
    job = OfficialSourceSyncJob(
        sec_client=AlwaysFailingSecClient(),
        alpha_vantage_client=FakeAlphaVantageClient(),
        document_repository=FakeDocumentRepository(),
        market_repository=FakeMarketRepository(),
        batch_repository=batch_repository,
        max_attempts=2,
    )

    with pytest.raises(RuntimeError, match='Source sync operation failed after 2 attempts'):
        job.sync_company(cik="1045810", ticker="NVDA", batch_id="batch-20260316")

    assert batch_repository.updated == [("batch-20260316", "failed")]