from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fin_insight_graph_agent.ingestion.document_repository import DocumentRepository
from fin_insight_graph_agent.ingestion.market_loader import DailyBarRecord
from fin_insight_graph_agent.ingestion.source_sync import OfficialSourceSyncJob
from fin_insight_graph_agent.storage.models.batch import BatchPublication
from fin_insight_graph_agent.storage.models.document import Chunk, Document
from fin_insight_graph_agent.storage.models.market import MarketDailyBar
from fin_insight_graph_agent.storage.repositories.batch_repository import BatchRepository
from fin_insight_graph_agent.storage.repositories.market_repository import MarketRepository


class FakeSecClient:
    def fetch_submissions(self, cik):
        return {'cik': cik, 'form': ['10-K']}

    def fetch_company_facts(self, cik):
        return {'cik': cik, 'facts': {'Revenue': 'mock'}}


class FakeNewsArticle:
    def __init__(self, title, url, summary):
        self.title = title
        self.url = url
        self.summary = summary
        self.source = 'Reuters'
        self.time_published = '20260313T120000'


class FakeAlphaVantageClient:
    def fetch_daily_adjusted(self, symbol, outputsize='compact'):
        return [
            DailyBarRecord(
                ticker=symbol,
                trade_date=date(2026, 3, 13),
                open_price=Decimal('118.00'),
                high_price=Decimal('120.00'),
                low_price=Decimal('117.50'),
                close_price=Decimal('119.50'),
                volume=1200000,
            )
        ]

    def fetch_news_sentiment(self, tickers, limit=20):
        symbol = tickers[0]
        return [
            FakeNewsArticle(
                title=f'{symbol} supplier capacity tightens',
                url=f'https://example.com/news/{symbol.lower()}-supply',
                summary='Capacity remains tight across packaging suppliers.',
            )
        ]


class FakeEntityProjector:
    def project(self, records):
        return None


class FakeChunkIndexer:
    def __init__(self):
        self.ensured = []
        self.indexed = []

    def ensure_collection(self, collection_name):
        self.ensured.append(collection_name)

    def index(self, collection_name, records):
        self.indexed.append((collection_name, records))


def test_source_sync_is_idempotent_when_rerunning_same_batch(db_engine):
    batch_repository = BatchRepository(db_engine)
    chunk_indexer = FakeChunkIndexer()
    job = OfficialSourceSyncJob(
        sec_client=FakeSecClient(),
        alpha_vantage_client=FakeAlphaVantageClient(),
        document_repository=DocumentRepository(db_engine),
        market_repository=MarketRepository(db_engine),
        batch_repository=batch_repository,
        entity_projector=FakeEntityProjector(),
        chunk_indexer=chunk_indexer,
    )

    first_summary = job.sync_company(cik='1045810', ticker='NVDA', batch_id='batch-20260313')
    second_summary = job.sync_company(cik='1045810', ticker='NVDA', batch_id='batch-20260313')

    with Session(db_engine) as session:
        document_count = session.scalar(select(func.count()).select_from(Document))
        chunk_count = session.scalar(select(func.count()).select_from(Chunk))
        market_count = session.scalar(select(func.count()).select_from(MarketDailyBar))
        batch_count = session.scalar(select(func.count()).select_from(BatchPublication))
        batch_status = session.get(BatchPublication, 'batch-20260313').status

    assert first_summary.document_count == second_summary.document_count == 3
    assert document_count == 3
    assert chunk_count == first_summary.indexed_chunk_count
    assert market_count == 1
    assert batch_count == 1
    assert batch_status == 'staged'
    assert len(chunk_indexer.indexed) == 2