from fin_insight_graph_agent.evaluation.runner import EvaluationRunner


class FakeEvalDependencies:
    dataset_root = "D:/myAgent/.worktrees/fin-insight-v1/tests/fixtures/evaluation"

    def persist_report(self, report):
        self.last_report = report


def test_evaluation_runner_emits_summary():
    deps = FakeEvalDependencies()
    runner = EvaluationRunner(deps)
    report = runner.run_suite("research_smoke")
    assert "faithfulness" in report.metric_names
    assert report.case_count == 1