from __future__ import annotations

from fastapi import FastAPI

from apps.api.routes.health import router as health_router
from apps.api.routes.query import router as query_router
from fin_insight_graph_agent.common.container import ApplicationContainer, build_container
from fin_insight_graph_agent.common.settings import AppSettings
from fin_insight_graph_agent.observability.middleware import ObservabilityMiddleware
from fin_insight_graph_agent.observability.tracing import setup_tracing


def create_app(container: ApplicationContainer | None = None) -> FastAPI:
    settings = AppSettings()
    setup_tracing(settings.service_name)
    app = FastAPI(title=settings.service_name)
    app.add_middleware(ObservabilityMiddleware)
    app.state.container = container or build_container()
    app.include_router(health_router)
    app.include_router(query_router)
    return app