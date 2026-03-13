from fin_insight_graph_agent.observability.metrics import (
    DAILY_BATCH_RUN_SECONDS,
    DAILY_BATCH_RUN_TOTAL,
    REQUEST_LATENCY_SECONDS,
    SOURCE_SYNC_RETRY_TOTAL,
)


def test_request_latency_metric_is_registered():
    assert REQUEST_LATENCY_SECONDS._name == 'figa_request_latency_seconds'


def test_daily_batch_metrics_are_registered():
    assert DAILY_BATCH_RUN_TOTAL._name == 'figa_daily_batch_run'
    assert DAILY_BATCH_RUN_SECONDS._name == 'figa_daily_batch_run_seconds'
    assert SOURCE_SYNC_RETRY_TOTAL._name == 'figa_source_sync_retry'