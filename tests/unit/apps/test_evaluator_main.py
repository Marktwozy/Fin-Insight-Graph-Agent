from apps.evaluator import main as evaluator_main
from fin_insight_graph_agent.evaluation.graph_benchmark import GraphRetrievalBenchmarkReport
from fin_insight_graph_agent.evaluation.metrics import MetricSummary


class FakeGraphBenchmarkRunner:
    def __init__(self, retriever, dataset_root):
        self.retriever = retriever
        self.dataset_root = dataset_root

    def run_suite(self, suite_name):
        return GraphRetrievalBenchmarkReport(
            suite_name=suite_name,
            case_count=2,
            summaries=[
                MetricSummary(name='multi_hop_entity_recall', value=0.50),
                MetricSummary(name='topic_hit_rate', value=0.80),
                MetricSummary(name='event_prefix_hit_rate', value=1.00),
                MetricSummary(name='event_explanation_coverage', value=1.00),
            ],
        )


class FakeEvaluationRunner:
    def __init__(self, deps):
        self.deps = deps

    def run_suite(self, suite_name):
        report = type('Report', (), {})()
        report.suite_name = suite_name
        report.case_count = 1
        report.summaries = [MetricSummary(name='faithfulness', value=1.00)]
        return report


class FakeResponseGenerator:
    model_version = 'openai-compatible:gpt-4.1-mini'


def test_evaluator_run_returns_nonzero_when_graph_thresholds_fail(monkeypatch):
    monkeypatch.setattr(evaluator_main, 'GraphRetrievalBenchmarkRunner', FakeGraphBenchmarkRunner)
    monkeypatch.setattr(evaluator_main, 'GraphRetriever', lambda client: object())
    monkeypatch.setattr(evaluator_main, 'build_neo4j_client', lambda: object())

    summary, exit_code = evaluator_main.run(
        [
            '--suite',
            'graph_retrieval_smoke',
            '--dataset-root',
            'D:/ignored',
            '--enforce-thresholds',
            '--graph-threshold',
            'topic_hit_rate=0.90',
            '--graph-threshold',
            'multi_hop_entity_recall=0.80',
        ]
    )

    assert exit_code == 1
    assert 'gate=fail' in summary
    assert 'topic_hit_rate' in summary
    assert 'multi_hop_entity_recall' in summary


def test_evaluator_run_uses_response_generator_model_version_for_standard_suites(monkeypatch):
    monkeypatch.setattr(
        evaluator_main,
        'build_response_generator',
        lambda settings: FakeResponseGenerator(),
    )
    monkeypatch.setattr(evaluator_main, 'EvaluationRunner', FakeEvaluationRunner)

    summary, exit_code = evaluator_main.run(
        [
            '--suite',
            'research_smoke',
            '--dataset-root',
            'D:/ignored',
        ]
    )

    assert exit_code == 0
    assert 'faithfulness=1.00' in summary