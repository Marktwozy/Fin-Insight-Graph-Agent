import json
import shutil
from pathlib import Path

from apps.worker import main as worker_main
from fin_insight_graph_agent.ingestion.daily_batch import DailyBatchRunSummary
from fin_insight_graph_agent.ingestion.source_sync import SourceSyncBatchSummary


class FakePublisher:
    def __init__(self, validation_result):
        self._validation_result = validation_result
        self.published_batch_ids = []
        self.validated_batch_ids = []

    def mark_validated(self, batch_id):
        self.validated_batch_ids.append(batch_id)
        return self._validation_result

    def publish(self, batch_id):
        self.published_batch_ids.append(batch_id)


class FakeValidationResult:
    def __init__(self, passed, suite_name='graph_retrieval_smoke'):
        self.passed = passed
        self.suite_name = suite_name
        self.metrics = {'topic_hit_rate': 1.0}
        self.threshold_failures = [{'metric_name': 'topic_hit_rate'}]


class FakeSourceSyncJob:
    def __init__(self):
        self.calls = []

    def sync_companies(self, targets, batch_id):
        self.calls.append((targets, batch_id))
        return SourceSyncBatchSummary(
            batch_id=batch_id,
            company_count=len(targets),
            tickers=[target.ticker for target in targets],
            document_count=6,
            market_bar_count=2,
            news_document_count=2,
            indexed_chunk_count=12,
        )


class FakeDailyBatchOrchestrator:
    def __init__(self):
        self.calls = []

    def run(self, *, targets, batch_id, publish_on_pass=True):
        self.calls.append((targets, batch_id, publish_on_pass))
        return DailyBatchRunSummary(
            batch_id=batch_id,
            sync_summary=SourceSyncBatchSummary(
                batch_id=batch_id,
                company_count=len(targets),
                tickers=[target.ticker for target in targets],
                document_count=9,
                market_bar_count=3,
                news_document_count=3,
                indexed_chunk_count=18,
            ),
            validation=FakeValidationResult(passed=True),
            published=publish_on_pass,
            status='published' if publish_on_pass else 'validated',
        )


def test_worker_publish_batch_returns_blocked_message_when_quality_gate_fails(monkeypatch):
    publisher = FakePublisher(FakeValidationResult(passed=False))
    monkeypatch.setattr(
        worker_main,
        'build_quality_gated_batch_publisher',
        lambda: publisher,
    )
    monkeypatch.setattr(
        worker_main,
        'build_parser',
        lambda: _args('publish-batch', 'batch-20260313'),
    )

    message = worker_main.main()

    assert publisher.validated_batch_ids == ['batch-20260313']
    assert publisher.published_batch_ids == []
    assert 'batch publish blocked' in message


def test_worker_publish_batch_promotes_batch_when_quality_gate_passes(monkeypatch):
    publisher = FakePublisher(FakeValidationResult(passed=True))
    monkeypatch.setattr(
        worker_main,
        'build_quality_gated_batch_publisher',
        lambda: publisher,
    )
    monkeypatch.setattr(
        worker_main,
        'build_parser',
        lambda: _args('publish-batch', 'batch-20260313'),
    )

    message = worker_main.main()

    assert publisher.validated_batch_ids == ['batch-20260313']
    assert publisher.published_batch_ids == ['batch-20260313']
    assert 'batch published' in message


def test_worker_source_sync_batch_loads_targets_file_and_returns_summary(monkeypatch):
    temp_root = Path('D:/myAgent/.worktrees/fin-insight-v1/tests/.tmp/worker-batch')
    if temp_root.exists():
        shutil.rmtree(temp_root)
    temp_root.mkdir(parents=True)
    targets_file = temp_root / 'targets.json'
    targets_file.write_text(
        json.dumps([
            {'ticker': 'nvda', 'cik': '1045810'},
            {'ticker': 'amd', 'cik': '2488'},
        ]),
        encoding='utf-8',
    )

    job = FakeSourceSyncJob()
    monkeypatch.setattr(worker_main, 'build_official_source_sync_job', lambda: job)
    monkeypatch.setattr(
        worker_main,
        'build_parser',
        lambda: _args('source-sync-batch', 'batch-20260313', str(targets_file)),
    )

    try:
        message = worker_main.main()
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    targets, batch_id = job.calls[0]
    assert batch_id == 'batch-20260313'
    assert [target.ticker for target in targets] == ['NVDA', 'AMD']
    assert 'source sync batch completed' in message
    assert 'tickers=NVDA,AMD' in message


def test_worker_daily_batch_uses_orchestrator_builder_and_batch_date(monkeypatch):
    temp_root = Path('D:/myAgent/.worktrees/fin-insight-v1/tests/.tmp/worker-daily-batch')
    if temp_root.exists():
        shutil.rmtree(temp_root)
    temp_root.mkdir(parents=True)
    targets_file = temp_root / 'targets.json'
    targets_file.write_text(
        json.dumps([
            {'ticker': 'nvda', 'cik': '1045810'},
            {'ticker': 'amd', 'cik': '2488'},
        ]),
        encoding='utf-8',
    )

    orchestrator = FakeDailyBatchOrchestrator()
    monkeypatch.setattr(
        worker_main,
        'build_daily_batch_orchestrator',
        lambda: orchestrator,
    )
    monkeypatch.setattr(
        worker_main,
        'build_parser',
        lambda: _args(
            'daily-batch',
            '',
            str(targets_file),
            batch_date='2026-03-13',
            skip_publish=True,
        ),
    )

    try:
        message = worker_main.main()
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    targets, batch_id, publish_on_pass = orchestrator.calls[0]
    assert [target.ticker for target in targets] == ['NVDA', 'AMD']
    assert batch_id == 'batch-20260313'
    assert publish_on_pass is False
    assert 'daily batch validated but not published' in message


def _args(job, batch_id, targets_file='', batch_date='', skip_publish=False):
    class Parser:
        @staticmethod
        def parse_args():
            class Args:
                pass

            args = Args()
            args.job = job
            args.batch_id = batch_id
            args.batch_date = batch_date
            args.ticker = 'NVDA'
            args.cik = '1045810'
            args.targets_file = targets_file
            args.skip_publish = skip_publish
            return args

    return Parser()
