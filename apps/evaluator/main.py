from __future__ import annotations

import argparse
from dataclasses import dataclass

from fin_insight_graph_agent.evaluation.graph_benchmark import GraphRetrievalBenchmarkRunner
from fin_insight_graph_agent.evaluation.runner import EvaluationRunner, SqlEvaluationPersister
from fin_insight_graph_agent.graph.graph_retriever import GraphRetriever
from fin_insight_graph_agent.graph.neo4j_client import build_neo4j_client

STANDARD_SUITES = ["research_smoke", "event_smoke"]
GRAPH_SUITES = ["graph_retrieval_smoke"]
ALL_SUITES = [*STANDARD_SUITES, *GRAPH_SUITES]


@dataclass(slots=True)
class EvaluatorDependencies:
    dataset_root: str

    def persist_report(self, report) -> None:
        SqlEvaluationPersister().persist_report(report)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Fin Insight evaluation suites")
    parser.add_argument("--suite", required=True, choices=ALL_SUITES)
    parser.add_argument(
        "--dataset-root",
        default="D:/myAgent/.worktrees/fin-insight-v1/tests/fixtures/evaluation",
    )
    return parser


def _render_summary(report) -> str:
    summary = ", ".join(f"{metric.name}={metric.value:.2f}" for metric in report.summaries)
    return f"suite={report.suite_name} cases={report.case_count} {summary}"


def main() -> str:
    args = build_parser().parse_args()
    if args.suite in GRAPH_SUITES:
        graph_report = GraphRetrievalBenchmarkRunner(
            retriever=GraphRetriever(build_neo4j_client()),
            dataset_root=args.dataset_root,
        ).run_suite(args.suite)
        return _render_summary(graph_report)

    deps = EvaluatorDependencies(dataset_root=args.dataset_root)
    standard_report = EvaluationRunner(deps).run_suite(args.suite)
    return _render_summary(standard_report)


if __name__ == "__main__":
    print(main())