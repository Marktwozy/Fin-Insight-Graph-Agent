from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_LATENCY_SECONDS = Histogram(
    'figa_request_latency_seconds',
    'Latency for API requests in seconds.',
    labelnames=('route', 'method'),
)
GRAPH_NODE_LATENCY_SECONDS = Histogram(
    'figa_graph_node_latency_seconds',
    'Latency for graph node execution in seconds.',
    labelnames=('node_name',),
)
TOKEN_INPUT_TOTAL = Counter(
    'figa_token_input_total',
    'Total prompt tokens consumed.',
    labelnames=('model',),
)
TOKEN_OUTPUT_TOTAL = Counter(
    'figa_token_output_total',
    'Total completion tokens consumed.',
    labelnames=('model',),
)
ESTIMATED_COST_USD_TOTAL = Counter(
    'figa_estimated_cost_usd_total',
    'Estimated model cost in USD.',
    labelnames=('model',),
)
RETRIEVAL_CANDIDATES = Histogram(
    'figa_retrieval_candidates',
    'Candidate bundle count returned by retrieval.',
    labelnames=('source',),
)
RERANKER_LATENCY_SECONDS = Histogram(
    'figa_reranker_latency_seconds',
    'Latency for reranker execution in seconds.',
)
REFLECTION_TRIGGER_TOTAL = Counter(
    'figa_reflection_trigger_total',
    'Count of reflection passes triggered.',
)
UNSUPPORTED_CLAIM_TOTAL = Counter(
    'figa_unsupported_claim_total',
    'Count of unsupported claims flagged by reflection.',
)
SOURCE_SYNC_RETRY_TOTAL = Counter(
    'figa_source_sync_retry_total',
    'Count of source sync retry attempts.',
    labelnames=('operation',),
)
DAILY_BATCH_RUN_TOTAL = Counter(
    'figa_daily_batch_run_total',
    'Count of daily batch runs by terminal status.',
    labelnames=('status',),
)
DAILY_BATCH_RUN_SECONDS = Histogram(
    'figa_daily_batch_run_seconds',
    'Latency for a daily batch run in seconds.',
    labelnames=('status',),
)



def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST