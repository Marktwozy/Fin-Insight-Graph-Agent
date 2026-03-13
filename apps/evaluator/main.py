from __future__ import annotations

import argparse
from dataclasses import dataclass

from fin_insight_graph_agent.evaluation.runner import EvaluationRunner, SqlEvaluationPersister


@dataclass(slots=True)
class EvaluatorDependencies:
    dataset_root: str

    def persist_report(self, report) -> None:
        SqlEvaluationPersister().persist_report(report)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Fin Insight evaluation suites")
    parser.add_argument("--suite", required=True, choices=["research_smoke", "event_smoke"])
    parser.add_argument(
        "--dataset-root",
        default="D:/myAgent/.worktrees/fin-insight-v1/tests/fixtures/evaluation",
    )
    return parser


def main() -> str:
    args = build_parser().parse_args()
    deps = EvaluatorDependencies(dataset_root=args.dataset_root)
    report = EvaluationRunner(deps).run_suite(args.suite)
    summary = ", ".join(f"{metric.name}={metric.value:.2f}" for metric in report.summaries)
    return f"suite={report.suite_name} cases={report.case_count} {summary}"


if __name__ == "__main__":
    print(main())