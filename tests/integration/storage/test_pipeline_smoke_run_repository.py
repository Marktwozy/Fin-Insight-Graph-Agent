from fin_insight_graph_agent.storage.repositories.pipeline_smoke_run_repository import (
    PipelineSmokeRunRepository,
)


def test_pipeline_smoke_run_repository_persists_and_completes_run(db_engine):
    repository = PipelineSmokeRunRepository(db_engine)

    created = repository.create_run(
        batch_id='batch-20260314',
        target_count=2,
        tickers_payload=['NVDA', 'AMD'],
    )
    completed = repository.complete_run(
        created.id,
        status='passed',
        batch_status='published',
        research_payload={'status': 'passed', 'citation_count': 1},
        event_payload={'status': 'passed', 'citation_count': 1},
        error_message=None,
        duration_seconds=1.5,
    )

    records = repository.list_for_batch('batch-20260314')

    assert completed.status == 'passed'
    assert completed.batch_status == 'published'
    assert completed.duration_seconds == 1.5
    assert completed.completed_at is not None
    assert len(records) == 1
    assert records[0].tickers_payload == ['NVDA', 'AMD']
    assert records[0].research_payload == {'status': 'passed', 'citation_count': 1}
    assert records[0].event_payload == {'status': 'passed', 'citation_count': 1}