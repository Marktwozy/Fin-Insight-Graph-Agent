from sqlalchemy import inspect


def test_initial_schema_contains_core_tables(db_engine):
    table_names = set(inspect(db_engine).get_table_names())
    expected = {
        'documents',
        'chunks',
        'market_daily_bars',
        'entities',
        'agent_runs',
        'memory_short_snapshots',
        'eval_runs',
        'batch_publications',
        'batch_quality_gate_runs',
        'daily_batch_runs',
        'pipeline_smoke_runs',
    }
    assert expected.issubset(table_names)