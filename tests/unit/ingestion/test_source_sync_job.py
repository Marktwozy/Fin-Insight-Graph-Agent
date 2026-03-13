from datetime import date
from decimal import Decimal

from fin_insight_graph_agent.ingestion.market_loader import DailyBarRecord
from fin_insight_graph_agent.ingestion.source_sync import OfficialSourceSyncJob


class FakeSecClient:
    def fetch_submissions(self, cik):
        return {"cik": cik, "form": ["10-K"]}

    def fetch_company_facts(self, cik):
        return {"cik": cik, "facts": {"Revenue": "mock"}}


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
        return [
            FakeNewsArticle(
                title="NVIDIA supplier capacity tightens",
                url="https://example.com/news/nvda-supply",
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

    def create_batch(self, batch_id, status):
        self.created.append((batch_id, status))
        return {"batch_id": batch_id, "status": status}


def test_official_source_sync_job_persists_sec_documents_market_bars_and_news():
    document_repository = FakeDocumentRepository()
    market_repository = FakeMarketRepository()
    batch_repository = FakeBatchRepository()
    job = OfficialSourceSyncJob(
        sec_client=FakeSecClient(),
        alpha_vantage_client=FakeAlphaVantageClient(),
        document_repository=document_repository,
        market_repository=market_repository,
        batch_repository=batch_repository,
    )

    summary = job.sync_company(cik="1045810", ticker="NVDA", batch_id="batch-20260313")

    assert batch_repository.created == [("batch-20260313", "staged")]
    assert len(document_repository.saved) == 3
    assert market_repository.saved[0][1] == "batch-20260313"
    assert summary.document_count == 3
    assert summary.market_bar_count == 1
    assert summary.news_document_count == 1