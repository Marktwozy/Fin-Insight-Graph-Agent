from fin_insight_graph_agent.observability.metrics import REQUEST_LATENCY_SECONDS


def test_request_latency_metric_is_registered():
    assert REQUEST_LATENCY_SECONDS._name == "figa_request_latency_seconds"