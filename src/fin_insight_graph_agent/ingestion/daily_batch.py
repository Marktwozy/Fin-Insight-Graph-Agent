from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from fin_insight_graph_agent.ingestion.publish_batch import BatchValidationResult
from fin_insight_graph_agent.ingestion.source_sync import (
    CompanySyncTarget,
    SourceSyncBatchSummary,
)


@dataclass(slots=True)
class DailyBatchRunSummary:
    batch_id: str
    sync_summary: SourceSyncBatchSummary
    validation: BatchValidationResult
    published: bool


class DailyBatchOrchestrator:
    def __init__(self, source_sync_job, publisher) -> None:
        self._source_sync_job = source_sync_job
        self._publisher = publisher

    def run(
        self,
        *,
        targets: list[CompanySyncTarget],
        batch_id: str,
        publish_on_pass: bool = True,
    ) -> DailyBatchRunSummary:
        sync_summary = self._source_sync_job.sync_companies(
            targets=targets,
            batch_id=batch_id,
        )
        validation = self._publisher.mark_validated(batch_id)
        published = False
        if validation.passed and publish_on_pass:
            self._publisher.publish(batch_id)
            published = True
        return DailyBatchRunSummary(
            batch_id=batch_id,
            sync_summary=sync_summary,
            validation=validation,
            published=published,
        )


def build_batch_id_for_date(batch_date: date) -> str:
    return f"batch-{batch_date.strftime('%Y%m%d')}"