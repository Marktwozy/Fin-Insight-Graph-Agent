from apps.api.main import create_app
from apps.worker.pipeline_smoke import PipelineSmokeRunner
from fin_insight_graph_agent.ingestion.daily_batch import DailyBatchRunSummary
from fin_insight_graph_agent.ingestion.source_sync import CompanySyncTarget, SourceSyncBatchSummary


class FakeValidationResult:
    def __init__(self, passed=True):
        self.passed = passed
        self.suite_name = 'graph_retrieval_smoke'
        self.metrics = {'topic_hit_rate': 1.0}
        self.thresholds = {'topic_hit_rate': 0.5}
        self.threshold_failures = []


class FakeDailyBatchOrchestrator:
    def __init__(self, status='published', published=True, passed=True):
        self.calls = []
        self._status = status
        self._published = published
        self._passed = passed

    def run(self, *, targets, batch_id, publish_on_pass=True):
        self.calls.append((targets, batch_id, publish_on_pass))
        return DailyBatchRunSummary(
            batch_id=batch_id,
            sync_summary=SourceSyncBatchSummary(
                batch_id=batch_id,
                company_count=len(targets),
                tickers=[target.ticker for target in targets],
                document_count=8,
                market_bar_count=2,
                news_document_count=2,
                indexed_chunk_count=10,
            ),
            validation=FakeValidationResult(passed=self._passed),
            published=self._published,
            status=self._status,
        )


class ResearchGraph:
    def invoke(self, payload):
        return {
            'citations': [{'doc_id': 'doc-1', 'chunk_id': 'chunk-1'}],
            'final_response': f"Grounded answer for {payload['question']}",
        }


class EventGraph:
    def invoke(self, payload):
        return {
            'citations': [{'doc_id': 'doc-2', 'chunk_id': 'chunk-2'}],
            'final_response': f"Event analysis for {payload['event_input']}",
        }


class FakeContainer:
    research_graph = ResearchGraph()
    event_graph = EventGraph()


class FakePipelineSmokeAuditRepository:
    def __init__(self):
        self.created = []
        self.completed = []

    def create_run(self, **kwargs):
        self.created.append(kwargs)
        return type('Record', (), {'id': 'smoke-run-1'})()

    def complete_run(self, run_id, **kwargs):
        self.completed.append((run_id, kwargs))
        return None


def test_pipeline_smoke_runs_daily_batch_and_both_query_routes():
    orchestrator = FakeDailyBatchOrchestrator()
    audit_repository = FakePipelineSmokeAuditRepository()
    runner = PipelineSmokeRunner(
        orchestrator,
        app_factory=create_app,
        container_factory=lambda: FakeContainer(),
        audit_repository=audit_repository,
    )

    summary = runner.run(
        targets=[CompanySyncTarget(ticker='NVDA', cik='1045810')],
        batch_id='batch-20260313',
    )

    assert orchestrator.calls == [([
        CompanySyncTarget(ticker='NVDA', cik='1045810')
    ], 'batch-20260313', True)]
    assert audit_repository.created[0]['batch_id'] == 'batch-20260313'
    assert audit_repository.created[0]['target_count'] == 1
    assert audit_repository.completed[0][1]['status'] == 'passed'
    assert audit_repository.completed[0][1]['batch_status'] == 'published'
    assert audit_repository.completed[0][1]['research_payload']['status'] == 'passed'
    assert audit_repository.completed[0][1]['event_payload']['status'] == 'passed'
    assert summary.batch_status == 'published'
    assert summary.research.status == 'passed'
    assert summary.research.citation_count == 1
    assert 'Grounded answer' in summary.research.final_response
    assert summary.event.status == 'passed'
    assert summary.event.citation_count == 1
    assert 'Event analysis' in summary.event.final_response


def test_pipeline_smoke_marks_blocked_audit_when_batch_is_not_published():
    audit_repository = FakePipelineSmokeAuditRepository()
    runner = PipelineSmokeRunner(
        FakeDailyBatchOrchestrator(status='failed_quality_gate', published=False, passed=False),
        app_factory=create_app,
        container_factory=lambda: FakeContainer(),
        audit_repository=audit_repository,
    )

    summary = runner.run(
        targets=[CompanySyncTarget(ticker='NVDA', cik='1045810')],
        batch_id='batch-20260313',
    )

    assert summary.batch_status == 'failed_quality_gate'
    assert summary.research.status == 'skipped'
    assert summary.event.status == 'skipped'
    assert audit_repository.completed[0][1]['status'] == 'blocked'
    assert audit_repository.completed[0][1]['batch_status'] == 'failed_quality_gate'