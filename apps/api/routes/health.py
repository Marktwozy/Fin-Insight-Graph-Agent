from __future__ import annotations

from fastapi import APIRouter, Response

from fin_insight_graph_agent.observability.metrics import render_metrics

router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics")
def metrics() -> Response:
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)