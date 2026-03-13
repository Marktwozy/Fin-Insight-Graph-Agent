from __future__ import annotations

import argparse
from dataclasses import dataclass

from fin_insight_graph_agent.evaluation.graph_benchmark import (
    DEFAULT_GRAPH_THRESHOLDS,
    GraphRetrievalBenchmarkRunner,
    evaluate_thresholds,
)
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
    parser.add_argument(
        "--enforce-thresholds",
        action="store_true",
        help="Fail graph retrieval suites when metric thresholds are missed.",
    )
    parser.add_argument(
        "--graph-threshold",
        action="append",
        default=[],
        metavar="METRIC=VALUE",
        help="Override a graph benchmark threshold, for example topic_hit_rate=0.95.",
    )
    return parser


def parse_graph_thresholds(raw_thresholds: list[str]) -> dict[str, float]:
    thresholds = dict(DEFAULT_GRAPH_THRESHOLDS)
    for raw_threshold in raw_thresholds:
        metric_name, separator, metric_value = raw_threshold.partition("=")
        if not separator:
            raise ValueError(f"Invalid threshold override: {raw_threshold}")
        thresholds[metric_name] = float(metric_value)
    return thresholds


def _render_summary(report) -> str:
    summary = ", ".join(f"{metric.name}={metric.value:.2f}" for metric in report.summaries)
    return f"suite={report.suite_name} cases={report.case_count} {summary}"


def _render_gate_suffix(gate_result) -> str:
    if gate_result.passed:
        return " gate=pass"
    failures = ",".join(
        f"{violation.metric_name}({violation.actual:.2f}<{violation.threshold:.2f})"
        for violation in gate_result.violations
    )
    return f" gate=fail threshold_failures={failures}"


def run(argv: list[str] | None = None) -> tuple[str, int]:
    args = build_parser().parse_args(argv)
    if args.suite in GRAPH_SUITES:
        graph_report = GraphRetrievalBenchmarkRunner(
            retriever=GraphRetriever(build_neo4j_client()),
            dataset_root=args.dataset_root,
        ).run_suite(args.suite)
        summary = _render_summary(graph_report)
        if args.enforce_thresholds:
            gate_result = evaluate_thresholds(
                graph_report,
                thresholds=parse_graph_thresholds(args.graph_threshold),
            )
            summary += _render_gate_suffix(gate_result)
            return summary, 0 if gate_result.passed else 1
        return summary, 0

    deps = EvaluatorDependencies(dataset_root=args.dataset_root)
    standard_report = EvaluationRunner(deps).run_suite(args.suite)
    return _render_summary(standard_report), 0


def main() -> str:
    summary, _ = run()
    return summary


if __name__ == "__main__":
    output, exit_code = run()
    print(output)
    raise SystemExit(exit_code)