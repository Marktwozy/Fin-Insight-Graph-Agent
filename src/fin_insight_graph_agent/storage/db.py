from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

DATABASE_URL = os.getenv(
    "FIGA_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/fin_insight",
)


def create_db_engine(database_url: str | None = None) -> Engine:
    return create_engine(database_url or DATABASE_URL, future=True)