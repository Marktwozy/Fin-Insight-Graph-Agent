from __future__ import annotations

from fin_insight_graph_agent.storage.repositories.batch_repository import BatchRepository


class BatchPublisher:
    def __init__(self, repository: BatchRepository) -> None:
        self._repository = repository

    def mark_validated(self, batch_id: str) -> None:
        batch = self._repository.get_batch(batch_id)
        if batch.status != "staged":
            raise ValueError("Only staged batches can be validated")
        self._repository.update_status(batch_id, "validated")

    def publish(self, batch_id: str) -> None:
        batch = self._repository.get_batch(batch_id)
        if batch.status != "validated":
            raise ValueError("Only validated batches can be published")
        self._repository.update_status(batch_id, "published")