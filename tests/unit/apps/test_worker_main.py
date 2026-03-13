from apps.worker import main as worker_main


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


def _args(job, batch_id):
    class Parser:
        @staticmethod
        def parse_args():
            class Args:
                pass

            args = Args()
            args.job = job
            args.batch_id = batch_id
            args.ticker = 'NVDA'
            args.cik = '1045810'
            return args

    return Parser()