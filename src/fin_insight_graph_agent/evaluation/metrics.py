from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from fin_insight_graph_agent.evaluation.datasets import EvaluationCase

RAGAS_METRIC_NAMES = (
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
)
BUSINESS_METRIC_NAMES = (
    "citation_coverage",
    "unsupported_claim_rate",
    "time_consistency_rate",
)


@dataclass(slots=True)
class MetricSummary:
    name: str
    value: float


class HeuristicRagasAdapter:
    def score_case(self, case: EvaluationCase) -> dict[str, float]:
        response_words = set(case.response.lower().split())
        reference_words = set(case.reference_answer.lower().split())
        context_words = set(" ".join(case.contexts).lower().split())
        overlap_with_reference = len(response_words & reference_words)
        overlap_with_context = len(response_words & context_words)
        denominator = max(len(reference_words), 1)
        context_denominator = max(len(context_words), 1)
        return {
            "faithfulness": min(overlap_with_context / max(len(response_words), 1), 1.0),
            "answer_relevancy": min(overlap_with_reference / denominator, 1.0),
            "context_precision": min(overlap_with_context / max(len(response_words), 1), 1.0),
            "context_recall": min(overlap_with_context / context_denominator, 1.0),
        }


class BusinessMetricAdapter:
    def score_case(self, case: EvaluationCase) -> dict[str, float]:
        unsupported_claim_rate = 1.0 if "definitely" in case.response.lower() else 0.0
        time_consistency_rate = 1.0 if case.batch_id else 0.0
        citation_coverage = 1.0 if case.citations else 0.0
        return {
            "citation_coverage": citation_coverage,
            "unsupported_claim_rate": unsupported_claim_rate,
            "time_consistency_rate": time_consistency_rate,
        }


def aggregate_metric_scores(case_scores: list[dict[str, float]]) -> list[MetricSummary]:
    metric_names = case_scores[0].keys() if case_scores else []
    return [
        MetricSummary(name=name, value=mean(score[name] for score in case_scores))
        for name in metric_names
    ]