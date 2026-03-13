from datetime import date

from fin_insight_graph_agent.ingestion.daily_batch import (
    DailyBatchOrchestrator,
    build_batch_id_for_date,
)
from fin_insight_graph_agent.ingestion.source_sync import CompanySyncTarget, SourceSyncBatchSummary


class FakeValidation:
    def __init__(self, passed, metrics, threshold_failures):
        self.passed = passed
        self.suite_name = 'graph_retrieval_smoke'
        self.metrics = metrics
        self.threshold_failures = threshold_failures


class FakeSourceSyncJob:
    def __init__(self):
        self.calls = []

    def sync_companies(self, *, targets, batch_id):
        self.calls.append((targets, batch_id))
        return SourceSyncBatchSummary(
            batch_id=batch_id,
            company_count=len(targets),
            tickers=[target.ticker for target in targets],
            document_count=9,
            market_bar_count=3,
            news_document_count=3,
            indexed_chunk_count=18,
        )


class FakePublisher:
    def __init__(self, validation):
        self.validation = validation
        self.validated = []
        self.published = []

    def mark_validated(self, batch_id):
        self.validated.append(batch_id)
        return self.validation

    def publish(self, batch_id):
        self.published.append(batch_id)



def test_daily_batch_orchestrator_syncs_validates_and_publishes():
    sync_job = FakeSourceSyncJob()
    validation = FakeValidation(
        passed=True,
        metrics={'topic_hit_rate': 1.0},
        threshold_failures=[],
    )
    publisher = FakePublisher(validation)
    orchestrator = DailyBatchOrchestrator(sync_job, publisher)

    summary = orchestrator.run(
        targets=[CompanySyncTarget(ticker='NVDA', cik='1045810')],
        batch_id='batch-20260313',
    )

    assert sync_job.calls[0][1] == 'batch-20260313'
    assert publisher.validated == ['batch-20260313']
    assert publisher.published == ['batch-20260313']
    assert summary.published is True



def test_daily_batch_orchestrator_skips_publish_when_requested():
    sync_job = FakeSourceSyncJob()
    validation = FakeValidation(
        passed=True,
        metrics={'topic_hit_rate': 1.0},
        threshold_failures=[],
    )
    publisher = FakePublisher(validation)
    orchestrator = DailyBatchOrchestrator(sync_job, publisher)

    summary = orchestrator.run(
        targets=[CompanySyncTarget(ticker='NVDA', cik='1045810')],
        batch_id='batch-20260313',
        publish_on_pass=False,
    )

    assert publisher.validated == ['batch-20260313']
    assert publisher.published == []
    assert summary.published is False



def test_daily_batch_orchestrator_does_not_publish_when_validation_fails():
    sync_job = FakeSourceSyncJob()
    validation = FakeValidation(
        passed=False,
        metrics={'topic_hit_rate': 0.0},
        threshold_failures=[{'metric_name': 'topic_hit_rate'}],
    )
    publisher = FakePublisher(validation)
    orchestrator = DailyBatchOrchestrator(sync_job, publisher)

    summary = orchestrator.run(
        targets=[CompanySyncTarget(ticker='NVDA', cik='1045810')],
        batch_id='batch-20260313',
    )

    assert publisher.published == []
    assert summary.published is False



def test_build_batch_id_for_date_formats_expected_pattern():
    batch_id = build_batch_id_for_date(date(2026, 3, 13))
    assert batch_id == 'batch-20260313'