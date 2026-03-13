from datetime import date
from decimal import Decimal
from pathlib import Path

from fin_insight_graph_agent.evaluation.batch_quality_gate import GraphBatchQualityGate
from fin_insight_graph_agent.graph.graph_retriever import GraphRetriever
from fin_insight_graph_agent.graph.neo4j_client import build_neo4j_client
from fin_insight_graph_agent.graph.project_entities import EntityProjector
from fin_insight_graph_agent.ingestion.connectors.alpha_vantage import NewsSentimentArticle
from fin_insight_graph_agent.ingestion.document_repository import DocumentRepository
from fin_insight_graph_agent.ingestion.market_loader import DailyBarRecord
from fin_insight_graph_agent.ingestion.publish_batch import BatchPublisher
from fin_insight_graph_agent.ingestion.source_sync import OfficialSourceSyncJob
from fin_insight_graph_agent.storage.repositories.batch_quality_gate_repository import (
    BatchQualityGateRepository,
)
from fin_insight_graph_agent.storage.repositories.batch_repository import BatchRepository
from fin_insight_graph_agent.storage.repositories.market_repository import MarketRepository


class FakeSecClient:
    def fetch_submissions(self, cik):
        return {'cik': cik, 'form': ['10-K']}

    def fetch_company_facts(self, cik):
        return {'cik': cik, 'facts': {'Revenue': 'mock'}}


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
        return [
            NewsSentimentArticle(
                title='U.S. export controls pressure NVIDIA and AMD supply',
                url='https://example.com/news/export-controls',
                time_published='20260313T150000',
                summary=(
                    'TSMC fab maintenance and tighter export restrictions may hit '
                    'NVIDIA and AMD GPU supply chains.'
                ),
                source='Reuters',
            )
        ]


def test_publish_batch_requires_quality_gate_pass_before_publish(db_engine):
    neo4j_client = build_neo4j_client()
    projector = EntityProjector(neo4j_client)
    projector.reset_database()
    batch_repository = BatchRepository(db_engine)
    job = OfficialSourceSyncJob(
        sec_client=FakeSecClient(),
        alpha_vantage_client=FakeAlphaVantageClient(),
        document_repository=DocumentRepository(db_engine),
        market_repository=MarketRepository(db_engine),
        batch_repository=batch_repository,
        entity_projector=projector,
    )
    job.sync_company(cik='1045810', ticker='NVDA', batch_id='batch-20260313')
    quality_gate = GraphBatchQualityGate(
        retriever=GraphRetriever(neo4j_client),
        audit_repository=BatchQualityGateRepository(db_engine),
        dataset_root=Path('D:/myAgent/.worktrees/fin-insight-v1/tests/fixtures/evaluation'),
    )
    publisher = BatchPublisher(batch_repository, quality_gate=quality_gate)

    decision = publisher.mark_validated('batch-20260313')
    publisher.publish('batch-20260313')

    batch_record = batch_repository.get_batch('batch-20260313')
    gate_runs = BatchQualityGateRepository(db_engine).list_for_batch('batch-20260313')
    assert decision.passed is True
    assert batch_record.status == 'published'
    assert gate_runs[-1].passed is True
    assert gate_runs[-1].suite_name == 'graph_retrieval_smoke'
    assert gate_runs[-1].metrics_payload['topic_hit_rate'] == 1.0


def test_publish_batch_marks_failed_quality_gate_and_records_audit_when_graph_gate_fails(db_engine):
    batch_repository = BatchRepository(db_engine)
    batch_repository.create_batch(batch_id='batch-20260314', status='staged')
    quality_gate = GraphBatchQualityGate(
        retriever=GraphRetriever(build_neo4j_client()),
        audit_repository=BatchQualityGateRepository(db_engine),
        dataset_root=Path('D:/myAgent/.worktrees/fin-insight-v1/tests/fixtures/evaluation'),
    )
    publisher = BatchPublisher(batch_repository, quality_gate=quality_gate)

    decision = publisher.mark_validated('batch-20260314')

    batch_record = batch_repository.get_batch('batch-20260314')
    gate_runs = BatchQualityGateRepository(db_engine).list_for_batch('batch-20260314')
    assert decision.passed is False
    assert batch_record.status == 'failed_quality_gate'
    assert gate_runs[-1].passed is False
    assert gate_runs[-1].threshold_failures_payload