from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from time import perf_counter
from typing import Any

from fin_insight_graph_agent.common.settings import AppSettings
from fin_insight_graph_agent.ingestion.publish_batch import (
    BatchValidationResult,
    build_quality_gated_batch_publisher,
)
from fin_insight_graph_agent.ingestion.source_sync import (
    CompanySyncTarget,
    SourceSyncBatchSummary,
    build_official_source_sync_job,
)
from fin_insight_graph_agent.observability.metrics import (
    DAILY_BATCH_RUN_SECONDS,
    DAILY_BATCH_RUN_TOTAL,
)
from fin_insight_graph_agent.storage.db import create_db_engine
from fin_insight_graph_agent.storage.repositories.daily_batch_run_repository import (
    DailyBatchRunRepository,
)


@dataclass(slots=True)
class DailyBatchRunSummary:
    batch_id: str
    sync_summary: SourceSyncBatchSummary
    validation: BatchValidationResult
    published: bool
    status: str


class DailyBatchOrchestrator:
    def __init__(self, source_sync_job, publisher, audit_repository=None) -> None:
        self._source_sync_job = source_sync_job
        self._publisher = publisher
        self._audit_repository = audit_repository

    def run(
        self,
        *,
        targets: list[CompanySyncTarget],
        batch_id: str,
        publish_on_pass: bool = True,
    ) -> DailyBatchRunSummary:
        started_at = perf_counter()
        audit_record = None
        if self._audit_repository is not None:
            audit_record = self._audit_repository.create_run(
                batch_id=batch_id,
                target_count=len(targets),
                tickers_payload=[target.ticker for target in targets],
            )

        sync_summary: SourceSyncBatchSummary | None = None
        validation: BatchValidationResult | None = None
        published = False
        status = 'failed'
        error_message: str | None = None
        try:
            sync_summary = self._source_sync_job.sync_companies(
                targets=targets,
                batch_id=batch_id,
            )
            validation = self._publisher.mark_validated(batch_id)
            if validation.passed and publish_on_pass:
                self._publisher.publish(batch_id)
                published = True
                status = 'published'
            elif validation.passed:
                status = 'validated'
            else:
                status = 'failed_quality_gate'
            return DailyBatchRunSummary(
                batch_id=batch_id,
                sync_summary=sync_summary,
                validation=validation,
                published=published,
                status=status,
            )
        except Exception as exc:  # noqa: BLE001
            error_message = str(exc)
            raise
        finally:
            duration_seconds = perf_counter() - started_at
            DAILY_BATCH_RUN_TOTAL.labels(status=status).inc()
            DAILY_BATCH_RUN_SECONDS.labels(status=status).observe(duration_seconds)
            if audit_record is not None:
                self._audit_repository.complete_run(
                    audit_record.id,
                    status=status,
                    published=published,
                    sync_summary_payload=_sync_summary_payload(sync_summary),
                    validation_payload=_validation_payload(validation),
                    error_message=error_message,
                    duration_seconds=duration_seconds,
                )



def build_batch_id_for_date(batch_date: date) -> str:
    return f"batch-{batch_date.strftime('%Y%m%d')}"



def build_daily_batch_orchestrator(
    settings: AppSettings | None = None,
) -> DailyBatchOrchestrator:
    resolved_settings = settings or AppSettings()
    engine = create_db_engine()
    return DailyBatchOrchestrator(
        build_official_source_sync_job(resolved_settings),
        build_quality_gated_batch_publisher(resolved_settings),
        audit_repository=DailyBatchRunRepository(engine),
    )



def _sync_summary_payload(summary: SourceSyncBatchSummary | None) -> dict[str, Any] | None:
    if summary is None:
        return None
    return {
        'batch_id': summary.batch_id,
        'company_count': summary.company_count,
        'tickers': summary.tickers,
        'document_count': summary.document_count,
        'market_bar_count': summary.market_bar_count,
        'news_document_count': summary.news_document_count,
        'indexed_chunk_count': summary.indexed_chunk_count,
    }



def _validation_payload(
    validation: BatchValidationResult | None,
) -> dict[str, Any] | None:
    if validation is None:
        return None
    return {
        'passed': validation.passed,
        'suite_name': validation.suite_name,
        'metrics': validation.metrics,
        'thresholds': validation.thresholds,
        'threshold_failures': validation.threshold_failures,
    }