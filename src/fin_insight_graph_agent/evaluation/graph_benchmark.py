from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from fin_insight_graph_agent.common.models import EvidenceBundle
from fin_insight_graph_agent.evaluation.metrics import MetricSummary, aggregate_metric_scores

GRAPH_SUITE_TO_FILE = {
    "graph_retrieval_smoke": "graph_retrieval_cases.jsonl",
}

DEFAULT_GRAPH_THRESHOLDS = {
    "multi_hop_entity_recall": 0.80,
    "topic_hit_rate": 0.90,
    "event_prefix_hit_rate": 0.90,
    "event_explanation_coverage": 1.00,
}


class GraphRetrievalCase(BaseModel):
    case_id: str
    batch_id: str
    query_entity_ids: list[str]
    expected_topics: list[str] = Field(default_factory=list)
    expected_event_prefixes: list[str] = Field(default_factory=list)
    expected_related_entities: list[str] = Field(default_factory=list)
    top_k: int = 5


@dataclass(slots=True)
class GraphRetrievalBenchmarkReport:
    suite_name: str
    case_count: int
    summaries: list[MetricSummary] = field(default_factory=list)

    @property
    def metric_names(self) -> list[str]:
        return [summary.name for summary in self.summaries]

    def metric_value(self, name: str) -> float:
        for summary in self.summaries:
            if summary.name == name:
                return summary.value
        raise KeyError(name)


@dataclass(slots=True)
class GraphThresholdViolation:
    metric_name: str
    actual: float
    threshold: float


@dataclass(slots=True)
class GraphBenchmarkGateResult:
    passed: bool
    violations: list[GraphThresholdViolation] = field(default_factory=list)


class GraphRetrievalBenchmarkRunner:
    def __init__(self, retriever: Any, dataset_root: str | Path) -> None:
        self._retriever = retriever
        self._dataset_root = Path(dataset_root)
        self.suite_to_file = dict(GRAPH_SUITE_TO_FILE)

    def run_suite(self, suite_name: str) -> GraphRetrievalBenchmarkReport:
        cases = self.load_suite(suite_name)
        case_scores = [self._score_case(case) for case in cases]
        return GraphRetrievalBenchmarkReport(
            suite_name=suite_name,
            case_count=len(cases),
            summaries=aggregate_metric_scores(case_scores),
        )

    def load_suite(self, suite_name: str) -> list[GraphRetrievalCase]:
        file_name = self.suite_to_file[suite_name]
        suite_path = self._dataset_root / file_name
        rows: list[GraphRetrievalCase] = []
        for line in suite_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rows.append(GraphRetrievalCase.model_validate(json.loads(line)))
        return rows

    def _score_case(self, case: GraphRetrievalCase) -> dict[str, float]:
        results = self._retriever.expand_entities(
            case.query_entity_ids,
            batch_id=case.batch_id,
            limit=case.top_k,
        )
        retrieved_topics = {
            str(result.citation_payload.get("topic"))
            for result in results
            if result.citation_payload.get("topic")
        }
        retrieved_event_ids = [
            str(result.citation_payload.get("event_id", "")) for result in results
        ]
        retrieved_related_entities = self._collect_related_entities(
            results,
            case.query_entity_ids,
        )
        event_explanation_coverage = self._event_explanation_coverage(results)
        return {
            "multi_hop_entity_recall": self._overlap_rate(
                case.expected_related_entities,
                retrieved_related_entities,
            ),
            "topic_hit_rate": self._overlap_rate(
                case.expected_topics,
                retrieved_topics,
            ),
            "event_prefix_hit_rate": self._prefix_hit_rate(
                case.expected_event_prefixes,
                retrieved_event_ids,
            ),
            "event_explanation_coverage": event_explanation_coverage,
        }

    @staticmethod
    def _collect_related_entities(
        results: list[EvidenceBundle],
        query_entity_ids: list[str],
    ) -> set[str]:
        related_entities: set[str] = set()
        query_entities = set(query_entity_ids)
        for result in results:
            related_entities.update(
                entity_id
                for entity_id in result.entity_refs
                if entity_id not in query_entities
            )
            payload_related = result.citation_payload.get("related_entities", [])
            if isinstance(payload_related, list):
                related_entities.update(str(entity_id) for entity_id in payload_related)
            elif payload_related:
                related_entities.add(str(payload_related))
        return related_entities

    @staticmethod
    def _event_explanation_coverage(results: list[EvidenceBundle]) -> float:
        if not results:
            return 0.0
        explained = 0
        for result in results:
            if result.citation_payload.get("event_id") and result.citation_payload.get(
                "event_name"
            ):
                explained += 1
        return explained / len(results)

    @staticmethod
    def _overlap_rate(expected: list[str], observed: set[str]) -> float:
        if not expected:
            return 1.0
        overlap = sum(1 for item in expected if item in observed)
        return overlap / len(expected)

    @staticmethod
    def _prefix_hit_rate(expected_prefixes: list[str], observed_ids: list[str]) -> float:
        if not expected_prefixes:
            return 1.0
        matched = 0
        for prefix in expected_prefixes:
            if any(observed_id.startswith(prefix) for observed_id in observed_ids):
                matched += 1
        return matched / len(expected_prefixes)


def evaluate_thresholds(
    report: GraphRetrievalBenchmarkReport,
    thresholds: dict[str, float] | None = None,
) -> GraphBenchmarkGateResult:
    resolved_thresholds = thresholds or DEFAULT_GRAPH_THRESHOLDS
    violations: list[GraphThresholdViolation] = []
    for metric_name, threshold in resolved_thresholds.items():
        actual = report.metric_value(metric_name)
        if actual < threshold:
            violations.append(
                GraphThresholdViolation(
                    metric_name=metric_name,
                    actual=actual,
                    threshold=threshold,
                )
            )
    return GraphBenchmarkGateResult(passed=not violations, violations=violations)