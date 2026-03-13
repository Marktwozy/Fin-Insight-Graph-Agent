from fin_insight_graph_agent.evaluation.runner import EvaluationRunner


class FakeEvalDependencies:
    dataset_root = 'D:/myAgent/.worktrees/fin-insight-v1/tests/fixtures/evaluation'
    prompt_version = 'prompt:v2'
    model_version = 'openai-compatible:gpt-4.1-mini'
    batch_id = 'batch-20260313'

    def persist_report(self, report):
        self.last_report = report


def test_evaluation_runner_emits_prompt_and_model_metadata():
    deps = FakeEvalDependencies()
    runner = EvaluationRunner(deps)

    report = runner.run_suite('research_smoke')

    assert report.prompt_version == 'prompt:v2'
    assert report.model_version == 'openai-compatible:gpt-4.1-mini'
    assert report.batch_id == 'batch-20260313'