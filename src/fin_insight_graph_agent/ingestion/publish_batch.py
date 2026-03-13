from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fin_insight_graph_agent.common.settings import AppSettings
from fin_insight_graph_agent.evaluation.batch_quality_gate import (
    BatchQualityGateDecision,
    GraphBatchQualityGate,
)
from fin_insight_graph_agent.graph.graph_retriever import GraphRetriever
from fin_insight_graph_agent.graph.neo4j_client import build_neo4j_client
from fin_insight_graph_agent.storage.db import create_db_engine
from fin_insight_graph_agent.storage.repositories.batch_quality_gate_repository import (
    BatchQualityGateRepository,
)
from fin_insight_graph_agent.storage.repositories.batch_repository import BatchRepository


@dataclass(slots=True)
class BatchValidationResult:
    passed: bool
    suite_name: str | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    thresholds: dict[str, float] = field(default_factory=dict)
    threshold_failures: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_gate_decision(cls, decision: BatchQualityGateDecision) -> BatchValidationResult:
        return cls(
            passed=decision.passed,
            suite_name=decision.suite_name,
            metrics=decision.metrics,
            thresholds=decision.thresholds,
            threshold_failures=decision.threshold_failures,
        )


class BatchPublisher:
    def __init__(
        self,
        repository: BatchRepository,
        quality_gate: Any | None = None,
    ) -> None:
        self._repository = repository
        self._quality_gate = quality_gate

    def mark_validated(self, batch_id: str) -> BatchValidationResult:
        batch = self._repository.get_batch(batch_id)
        if batch.status not in {"staged", "failed_quality_gate"}:
            raise ValueError("Only staged or failed_quality_gate batches can be validated")

        if self._quality_gate is None:
            self._repository.update_status(batch_id, "validated")
            return BatchValidationResult(passed=True)

        decision = self._quality_gate.evaluate_batch(batch_id)
        next_status = "validated" if decision.passed else "failed_quality_gate"
        self._repository.update_status(batch_id, next_status)
        return BatchValidationResult.from_gate_decision(decision)

    def publish(self, batch_id: str) -> None:
        batch = self._repository.get_batch(batch_id)
        if batch.status != "validated":
            raise ValueError("Only validated batches can be published")
        self._repository.update_status(batch_id, "published")


def build_quality_gated_batch_publisher(
    settings: AppSettings | None = None,
) -> BatchPublisher:
    resolved_settings = settings or AppSettings()
    engine = create_db_engine()
    repository = BatchRepository(engine)
    quality_gate = GraphBatchQualityGate(
        retriever=GraphRetriever(build_neo4j_client()),
        audit_repository=BatchQualityGateRepository(engine),
        dataset_root=resolved_settings.evaluation_dataset_root,
        suite_name=resolved_settings.graph_benchmark_suite,
    )
    return BatchPublisher(repository, quality_gate=quality_gate)