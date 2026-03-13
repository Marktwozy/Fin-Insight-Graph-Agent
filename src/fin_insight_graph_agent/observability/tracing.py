from __future__ import annotations

from functools import lru_cache

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider


@lru_cache(maxsize=1)
def setup_tracing(service_name: str):
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    trace.set_tracer_provider(provider)
    return provider


def get_tracer(name: str = "fin_insight_graph_agent"):
    return trace.get_tracer(name)