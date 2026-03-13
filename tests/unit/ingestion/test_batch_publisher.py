from dataclasses import dataclass, field

from fin_insight_graph_agent.ingestion.publish_batch import BatchPublisher


@dataclass(slots=True)
class FakeBatchRecord:
    batch_id: str
    status: str


class FakeBatchRepository:
    def __init__(self):
        self._batches = {}

    def create_batch(self, batch_id, status):
        batch = FakeBatchRecord(batch_id=batch_id, status=status)
        self._batches[batch_id] = batch
        return batch

    def get_batch(self, batch_id):
        return self._batches[batch_id]

    def update_status(self, batch_id, status):
        self._batches[batch_id].status = status
        return self._batches[batch_id]


@dataclass(slots=True)
class FakeGateResult:
    suite_name: str
    passed: bool
    metrics: dict[str, float]
    thresholds: dict[str, float] = field(default_factory=dict)
    threshold_failures: list[dict[str, float]] = field(default_factory=list)


class FakeQualityGate:
    def __init__(self, result):
        self._result = result
        self.seen_batch_ids = []

    def evaluate_batch(self, batch_id):
        self.seen_batch_ids.append(batch_id)
        return self._result


def test_mark_validated_marks_batch_validated_when_quality_gate_passes():
    repository = FakeBatchRepository()
    repository.create_batch('batch-20260313', 'staged')
    quality_gate = FakeQualityGate(
        FakeGateResult(
            suite_name='graph_retrieval_smoke',
            passed=True,
            metrics={'topic_hit_rate': 1.0},
            thresholds={'topic_hit_rate': 0.9},
        )
    )
    publisher = BatchPublisher(repository, quality_gate=quality_gate)

    decision = publisher.mark_validated('batch-20260313')

    assert decision.passed is True
    assert quality_gate.seen_batch_ids == ['batch-20260313']
    assert repository.get_batch('batch-20260313').status == 'validated'


def test_mark_validated_marks_batch_failed_quality_gate_when_quality_gate_fails():
    repository = FakeBatchRepository()
    repository.create_batch('batch-20260313', 'staged')
    quality_gate = FakeQualityGate(
        FakeGateResult(
            suite_name='graph_retrieval_smoke',
            passed=False,
            metrics={'topic_hit_rate': 0.5},
            thresholds={'topic_hit_rate': 0.9},
            threshold_failures=[{'metric_name': 'topic_hit_rate', 'actual': 0.5, 'threshold': 0.9}],
        )
    )
    publisher = BatchPublisher(repository, quality_gate=quality_gate)

    decision = publisher.mark_validated('batch-20260313')

    assert decision.passed is False
    assert repository.get_batch('batch-20260313').status == 'failed_quality_gate'