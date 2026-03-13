import json
from pathlib import Path
from uuid import uuid4

from fin_insight_graph_agent.common.models import EvidenceBundle
from fin_insight_graph_agent.evaluation.graph_benchmark import GraphRetrievalBenchmarkRunner


class FakeGraphRetriever:
    def expand_entities(self, entity_ids, batch_id, limit=5):
        return [
            EvidenceBundle(
                evidence_id=entity_ids[0],
                source_type="graph",
                content="AMD is linked to an export control event touching NVIDIA and TSMC.",
                score_raw=1.0,
                entity_refs=["company:amd", "company:nvda", "company:tsmc"],
                time_refs=["2026-03-13"],
                market_refs=["ticker:AMD"],
                citation_payload={
                    "entity_id": "company:amd",
                    "event_id": "event:export_control:amd-supply",
                    "event_name": "U.S. export controls pressure NVIDIA and AMD supply",
                    "topic": "export_controls",
                    "related_entities": ["company:nvda", "company:tsmc"],
                },
                batch_id=batch_id,
                retrieval_path="neo4j.neighborhood",
            )
        ]


def test_graph_benchmark_runner_scores_multihop_topic_and_event_quality():
    dataset_root = Path(__file__).resolve().parents[1] / ".tmp"
    dataset_root.mkdir(parents=True, exist_ok=True)
    dataset_path = dataset_root / f"graph_retrieval_cases_{uuid4().hex}.jsonl"
    dataset_path.write_text(
        json.dumps(
            {
                "case_id": "graph-1",
                "batch_id": "batch-20260313",
                "query_entity_ids": ["company:amd"],
                "expected_topics": ["export_controls"],
                "expected_event_prefixes": ["event:export_control"],
                "expected_related_entities": ["company:nvda", "company:tsmc"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    runner = GraphRetrievalBenchmarkRunner(
        retriever=FakeGraphRetriever(),
        dataset_root=dataset_root,
    )
    runner.suite_to_file["graph_retrieval_smoke"] = dataset_path.name
    report = runner.run_suite("graph_retrieval_smoke")

    assert report.case_count == 1
    assert report.metric_value("multi_hop_entity_recall") == 1.0
    assert report.metric_value("topic_hit_rate") == 1.0
    assert report.metric_value("event_prefix_hit_rate") == 1.0
    assert report.metric_value("event_explanation_coverage") == 1.0