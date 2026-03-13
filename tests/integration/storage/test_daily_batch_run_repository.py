from fin_insight_graph_agent.storage.repositories.daily_batch_run_repository import (
    DailyBatchRunRepository,
)


def test_daily_batch_run_repository_persists_and_completes_run(db_engine):
    repository = DailyBatchRunRepository(db_engine)

    created = repository.create_run(
        batch_id='batch-20260313',
        target_count=2,
        tickers_payload=['NVDA', 'AMD'],
    )
    completed = repository.complete_run(
        created.id,
        status='published',
        published=True,
        sync_summary_payload={'document_count': 6},
        validation_payload={'passed': True, 'suite_name': 'graph_retrieval_smoke'},
        error_message=None,
        duration_seconds=1.25,
    )

    records = repository.list_for_batch('batch-20260313')

    assert completed.status == 'published'
    assert completed.published is True
    assert completed.duration_seconds == 1.25
    assert completed.completed_at is not None
    assert len(records) == 1
    assert records[0].tickers_payload == ['NVDA', 'AMD']
    assert records[0].sync_summary_payload == {'document_count': 6}
    assert records[0].validation_payload == {
        'passed': True,
        'suite_name': 'graph_retrieval_smoke',
    }
