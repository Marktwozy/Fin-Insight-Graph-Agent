from fin_insight_graph_agent.ingestion.publish_batch import BatchPublisher
from fin_insight_graph_agent.storage.repositories.batch_repository import BatchRepository


def test_publish_batch_requires_validation_before_publish(db_engine):
    repository = BatchRepository(db_engine)
    publisher = BatchPublisher(repository)

    repository.create_batch(batch_id="batch-20260313", status="staged")
    publisher.mark_validated("batch-20260313")
    publisher.publish("batch-20260313")

    batch_record = repository.get_batch("batch-20260313")
    assert batch_record.status == "published"