from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1", tags=["query"])


class QueryRequest(BaseModel):
    question: str | None = None
    event_input: str | None = None
    batch_id: str


class QueryResponse(BaseModel):
    trace_id: str
    route: str
    citations: list[dict[str, str]] = Field(default_factory=list)
    final_response: str


@router.post("/query", response_model=QueryResponse)
def query_endpoint(payload: QueryRequest, request: Request) -> QueryResponse:
    container = request.app.state.container
    trace_id = uuid4().hex
    if payload.event_input and not payload.question:
        route = "event"
        result = container.event_graph.invoke(
            {"event_input": payload.event_input, "batch_id": payload.batch_id}
        )
    else:
        route = "research"
        result = container.research_graph.invoke(
            {"question": payload.question or "", "batch_id": payload.batch_id}
        )
    return QueryResponse(
        trace_id=trace_id,
        route=route,
        citations=result.get("citations", []),
        final_response=result.get("final_response", ""),
    )