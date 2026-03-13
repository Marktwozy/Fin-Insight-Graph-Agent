from pathlib import Path

from fin_insight_graph_agent.common.models import EvidenceBundle
from fin_insight_graph_agent.evaluation.graph_benchmark import (
    GraphRetrievalBenchmarkReport,
    GraphRetrievalBenchmarkRunner,
    evaluate_thresholds,
)
from fin_insight_graph_agent.evaluation.metrics import MetricSummary


class FakeGraphRetriever:
    def expand_entities(self, entity_ids, batch_id, limit=5):
        return [
            EvidenceBundle(
                evidence_id=entity_ids[0],
                source_type="graph",
                content=(
                    "Company is linked to an export control event touching "
                    "NVIDIA, AMD, and TSMC."
                ),
                score_raw=1.0,
                entity_refs=["company:amd", "company:nvda", "company:tsmc"],
                time_refs=["2026-03-13"],
                market_refs=["ticker:AMD"],
                citation_payload={
                    "entity_id": entity_ids[0],
                    "event_id": "event:export_control:amd-supply",
                    "event_name": "U.S. export controls pressure NVIDIA and AMD supply",
                    "topic": "export_controls",
                    "related_entities": ["company:nvda", "company:tsmc", "company:amd"],
                },
                batch_id=batch_id,
                retrieval_path="neo4j.neighborhood",
            )
        ]


def test_graph_benchmark_runner_scores_multi_case_topic_and_event_quality():
    dataset_root = Path(__file__).resolve().parents[1] / "fixtures" / "evaluation"
    runner = GraphRetrievalBenchmarkRunner(
        retriever=FakeGraphRetriever(),
        dataset_root=dataset_root,
    )
    report = runner.run_suite("graph_retrieval_smoke")

    assert report.case_count == 2
    assert report.metric_value("multi_hop_entity_recall") == 1.0
    assert report.metric_value("topic_hit_rate") == 1.0
    assert report.metric_value("event_prefix_hit_rate") == 1.0
    assert report.metric_value("event_explanation_coverage") == 1.0


def test_graph_benchmark_threshold_gate_reports_failures():
    report = GraphRetrievalBenchmarkReport(
        suite_name="graph_retrieval_smoke",
        case_count=2,
        summaries=[
            MetricSummary(name="multi_hop_entity_recall", value=0.50),
            MetricSummary(name="topic_hit_rate", value=1.00),
            MetricSummary(name="event_prefix_hit_rate", value=1.00),
            MetricSummary(name="event_explanation_coverage", value=0.50),
        ],
    )

    gate_result = evaluate_thresholds(
        report,
        thresholds={
            "multi_hop_entity_recall": 0.80,
            "event_explanation_coverage": 1.00,
        },
    )

    assert gate_result.passed is False
    assert [violation.metric_name for violation in gate_result.violations] == [
        "multi_hop_entity_recall",
        "event_explanation_coverage",
    ]