from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fin_insight_graph_agent.evaluation.graph_benchmark import (
    DEFAULT_GRAPH_THRESHOLDS,
    GraphRetrievalBenchmarkRunner,
    evaluate_thresholds,
)
from fin_insight_graph_agent.storage.repositories.batch_quality_gate_repository import (
    BatchQualityGateRepository,
)


@dataclass(slots=True)
class BatchQualityGateDecision:
    suite_name: str
    passed: bool
    metrics: dict[str, float] = field(default_factory=dict)
    thresholds: dict[str, float] = field(default_factory=dict)
    threshold_failures: list[dict[str, Any]] = field(default_factory=list)


class GraphBatchQualityGate:
    def __init__(
        self,
        *,
        retriever: Any,
        audit_repository: BatchQualityGateRepository,
        dataset_root: str | Path,
        suite_name: str = "graph_retrieval_smoke",
        thresholds: dict[str, float] | None = None,
    ) -> None:
        self._retriever = retriever
        self._audit_repository = audit_repository
        self._dataset_root = Path(dataset_root)
        self._suite_name = suite_name
        self._thresholds = thresholds or dict(DEFAULT_GRAPH_THRESHOLDS)

    def evaluate_batch(self, batch_id: str) -> BatchQualityGateDecision:
        report = GraphRetrievalBenchmarkRunner(
            retriever=self._retriever,
            dataset_root=self._dataset_root,
        ).run_suite(self._suite_name, batch_id=batch_id)
        gate_result = evaluate_thresholds(report, thresholds=self._thresholds)
        decision = BatchQualityGateDecision(
            suite_name=self._suite_name,
            passed=gate_result.passed,
            metrics={summary.name: summary.value for summary in report.summaries},
            thresholds=dict(self._thresholds),
            threshold_failures=[
                {
                    "metric_name": violation.metric_name,
                    "actual": violation.actual,
                    "threshold": violation.threshold,
                }
                for violation in gate_result.violations
            ],
        )
        self._audit_repository.create_run(
            batch_id=batch_id,
            suite_name=decision.suite_name,
            passed=decision.passed,
            metrics_payload=decision.metrics,
            thresholds_payload=decision.thresholds,
            threshold_failures_payload=decision.threshold_failures,
        )
        return decision