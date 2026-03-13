from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from fin_insight_graph_agent.observability.metrics import REQUEST_LATENCY_SECONDS
from fin_insight_graph_agent.observability.tracing import get_tracer


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        trace_id = request.headers.get("x-trace-id") or uuid4().hex
        request.state.trace_id = trace_id
        tracer = get_tracer()
        start = perf_counter()
        with tracer.start_as_current_span(f"http.{request.method.lower()}") as span:
            span.set_attribute("figa.trace_id", trace_id)
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.route", request.url.path)
            response = await call_next(request)
        duration = perf_counter() - start
        REQUEST_LATENCY_SECONDS.labels(
            route=request.url.path,
            method=request.method,
        ).observe(duration)
        response.headers["x-trace-id"] = trace_id
        return response