from datetime import date
from decimal import Decimal
from pathlib import Path

from fin_insight_graph_agent.evaluation.graph_benchmark import GraphRetrievalBenchmarkRunner
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


def test_graph_benchmark_runner_scores_real_source_sync_projection(db_engine):
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

    dataset_root = Path(__file__).resolve().parents[2] / "fixtures" / "evaluation"
    runner = GraphRetrievalBenchmarkRunner(
        retriever=GraphRetriever(neo4j_client),
        dataset_root=dataset_root,
    )
    report = runner.run_suite("graph_retrieval_smoke")

    assert report.case_count == 2
    assert report.metric_value("topic_hit_rate") == 1.0
    assert report.metric_value("event_prefix_hit_rate") == 1.0
    assert report.metric_value("multi_hop_entity_recall") == 1.0
    assert report.metric_value("event_explanation_coverage") == 1.0