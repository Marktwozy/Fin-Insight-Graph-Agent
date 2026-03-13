from __future__ import annotations

from fastapi import FastAPI

from apps.api.routes.health import router as health_router
from apps.api.routes.query import router as query_router
from fin_insight_graph_agent.common.container import ApplicationContainer, build_container
from fin_insight_graph_agent.common.settings import AppSettings


def create_app(container: ApplicationContainer | None = None) -> FastAPI:
    settings = AppSettings()
    app = FastAPI(title=settings.service_name)
    app.state.container = container or build_container()
    app.include_router(health_router)
    app.include_router(query_router)
    return app