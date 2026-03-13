from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from fin_insight_graph_agent.evaluation.datasets import load_suite
from fin_insight_graph_agent.evaluation.metrics import (
    BusinessMetricAdapter,
    HeuristicRagasAdapter,
    MetricSummary,
    aggregate_metric_scores,
)
from fin_insight_graph_agent.storage.db import create_db_engine
from fin_insight_graph_agent.storage.models.evaluation import EvalRun


@dataclass(slots=True)
class EvaluationReport:
    suite_name: str
    case_count: int
    batch_id: str = 'evaluation'
    prompt_version: str = 'prompt:v1'
    model_version: str = 'heuristic'
    summaries: list[MetricSummary] = field(default_factory=list)

    @property
    def metric_names(self) -> list[str]:
        return [summary.name for summary in self.summaries]

    def metric_value(self, name: str) -> float:
        for summary in self.summaries:
            if summary.name == name:
                return summary.value
        raise KeyError(name)


class SqlEvaluationPersister:
    def persist_report(self, report: EvaluationReport) -> None:
        engine = create_db_engine()
        with Session(engine) as session:
            faithfulness = 0.0
            if 'faithfulness' in report.metric_names:
                faithfulness = report.metric_value('faithfulness')
            session.add(
                EvalRun(
                    id=uuid.uuid4().hex,
                    suite_name=report.suite_name,
                    batch_id=report.batch_id,
                    prompt_version=report.prompt_version,
                    model_version=report.model_version,
                    faithfulness_score=faithfulness,
                )
            )
            session.commit()


class EvaluationRunner:
    def __init__(self, dependencies):
        self.dependencies = dependencies
        self.ragas_adapter = getattr(dependencies, 'ragas_adapter', HeuristicRagasAdapter())
        self.business_adapter = getattr(
            dependencies,
            'business_adapter',
            BusinessMetricAdapter(),
        )

    def run_suite(self, suite_name: str) -> EvaluationReport:
        dataset_root = self.dependencies.dataset_root
        cases = load_suite(dataset_root, suite_name)
        case_scores: list[dict[str, float]] = []
        for case in cases:
            scores = self.ragas_adapter.score_case(case)
            scores.update(self.business_adapter.score_case(case))
            case_scores.append(scores)
        report = EvaluationReport(
            suite_name=suite_name,
            case_count=len(cases),
            batch_id=getattr(self.dependencies, 'batch_id', 'evaluation'),
            prompt_version=getattr(self.dependencies, 'prompt_version', 'prompt:v1'),
            model_version=getattr(self.dependencies, 'model_version', 'heuristic'),
            summaries=aggregate_metric_scores(case_scores),
        )
        persist_report = getattr(self.dependencies, 'persist_report', None)
        if persist_report is not None:
            persist_report(report)
        return report