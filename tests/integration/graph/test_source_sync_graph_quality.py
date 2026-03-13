from datetime import date
from decimal import Decimal

from fin_insight_graph_agent.graph.graph_retriever import GraphRetriever
from fin_insight_graph_agent.graph.neo4j_client import build_neo4j_client
from fin_insight_graph_agent.graph.project_entities import EntityProjector
from fin_insight_graph_agent.ingestion.connectors.alpha_vantage import NewsSentimentArticle
from fin_insight_graph_agent.ingestion.document_repository import DocumentRepository
from fin_insight_graph_agent.ingestion.market_loader import DailyBarRecord
from fin_insight_graph_agent.ingestion.source_sync import OfficialSourceSyncJob
from fin_insight_graph_agent.storage.repositories.batch_repository import BatchRepository
from fin_insight_graph_agent.storage.repositories.market_repository import MarketRepository


class FakeSecClient:
    def fetch_submissions(self, cik):
        return {"cik": cik, "form": ["10-K"]}

    def fetch_company_facts(self, cik):
        return {"cik": cik, "facts": {"Revenue": "mock"}}


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
            NewsSentimentArticle(
                title="U.S. export controls pressure NVIDIA and AMD supply",
                url="https://example.com/news/export-controls",
                time_published="20260313T150000",
                summary=(
                    "TSMC fab maintenance and tighter export restrictions may hit "
                    "NVIDIA and AMD GPU supply chains."
                ),
                source="Reuters",
            )
        ]


def test_source_sync_projects_news_into_neo4j_and_graph_retriever_returns_auditable_evidence(
    db_engine,
):
    neo4j_client = build_neo4j_client()
    projector = EntityProjector(neo4j_client)
    projector.reset_database()

    job = OfficialSourceSyncJob(
        sec_client=FakeSecClient(),
        alpha_vantage_client=FakeAlphaVantageClient(),
        document_repository=DocumentRepository(db_engine),
        market_repository=MarketRepository(db_engine),
        batch_repository=BatchRepository(db_engine),
        entity_projector=projector,
    )
    job.sync_company(cik="1045810", ticker="NVDA", batch_id="batch-20260313")

    retriever = GraphRetriever(neo4j_client)
    amd_results = retriever.expand_entities(["company:amd"], batch_id="batch-20260313")
    tsmc_results = retriever.expand_entities(["company:tsmc"], batch_id="batch-20260313")

    assert amd_results
    assert tsmc_results
    assert amd_results[0].retrieval_path == "neo4j.neighborhood"
    assert amd_results[0].citation_payload["topic"] == "export_controls"
    assert (
        amd_results[0].citation_payload["event_name"]
        == "U.S. export controls pressure NVIDIA and AMD supply"
    )
    assert amd_results[0].citation_payload["event_id"].startswith("event:export_control")