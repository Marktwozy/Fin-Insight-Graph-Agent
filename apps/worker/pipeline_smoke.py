from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi.testclient import TestClient

from apps.api.main import create_app
from fin_insight_graph_agent.common.container import build_container
from fin_insight_graph_agent.common.settings import AppSettings
from fin_insight_graph_agent.ingestion.daily_batch import (
    build_daily_batch_orchestrator,
)
from fin_insight_graph_agent.ingestion.source_sync import CompanySyncTarget

DEFAULT_RESEARCH_QUESTION = 'What supply risks does NVIDIA face?'
DEFAULT_EVENT_INPUT = 'A packaging bottleneck hits TSMC CoWoS capacity'


@dataclass(slots=True)
class QuerySmokeResult:
    route: str
    status: str
    citation_count: int
    final_response: str
    trace_id: str
    error_message: str | None = None


@dataclass(slots=True)
class PipelineSmokeSummary:
    batch_id: str
    batch_status: str
    research: QuerySmokeResult
    event: QuerySmokeResult


class PipelineSmokeRunner:
    def __init__(
        self,
        daily_batch_orchestrator,
        *,
        app_factory: Callable[[Any], Any] = create_app,
        container_factory: Callable[[], Any] = build_container,
    ) -> None:
        self._daily_batch_orchestrator = daily_batch_orchestrator
        self._app_factory = app_factory
        self._container_factory = container_factory

    def run(
        self,
        *,
        targets: list[CompanySyncTarget],
        batch_id: str,
        research_question: str = '',
        event_input: str = '',
    ) -> PipelineSmokeSummary:
        batch_summary = self._daily_batch_orchestrator.run(
            targets=targets,
            batch_id=batch_id,
            publish_on_pass=True,
        )
        if not batch_summary.validation.passed or not batch_summary.published:
            return PipelineSmokeSummary(
                batch_id=batch_id,
                batch_status=batch_summary.status,
                research=_skipped_result('research'),
                event=_skipped_result('event'),
            )

        app = self._app_factory(self._container_factory())
        with TestClient(app) as client:
            research = self._run_query_smoke(
                client,
                route='research',
                payload={
                    'question': research_question or DEFAULT_RESEARCH_QUESTION,
                    'batch_id': batch_id,
                },
            )
            event = self._run_query_smoke(
                client,
                route='event',
                payload={
                    'event_input': event_input or DEFAULT_EVENT_INPUT,
                    'batch_id': batch_id,
                },
            )
        return PipelineSmokeSummary(
            batch_id=batch_id,
            batch_status=batch_summary.status,
            research=research,
            event=event,
        )

    def _run_query_smoke(
        self,
        client: TestClient,
        *,
        route: str,
        payload: dict[str, str],
    ) -> QuerySmokeResult:
        response = client.post('/v1/query', json=payload)
        if response.status_code != 200:
            return QuerySmokeResult(
                route=route,
                status='failed',
                citation_count=0,
                final_response='',
                trace_id='',
                error_message=f'HTTP {response.status_code}',
            )
        body = response.json()
        citations = body.get('citations', [])
        final_response = body.get('final_response', '')
        trace_id = body.get('trace_id', '')
        status = 'passed' if citations and final_response else 'failed'
        return QuerySmokeResult(
            route=route,
            status=status,
            citation_count=len(citations),
            final_response=final_response,
            trace_id=trace_id,
            error_message=None if status == 'passed' else 'missing response body',
        )


def build_pipeline_smoke_runner(
    settings: AppSettings | None = None,
) -> PipelineSmokeRunner:
    resolved_settings = settings or AppSettings()
    return PipelineSmokeRunner(
        build_daily_batch_orchestrator(resolved_settings),
        app_factory=create_app,
        container_factory=lambda: build_container(resolved_settings),
    )


def _skipped_result(route: str) -> QuerySmokeResult:
    return QuerySmokeResult(
        route=route,
        status='skipped',
        citation_count=0,
        final_response='',
        trace_id='',
        error_message='batch not published',
    )