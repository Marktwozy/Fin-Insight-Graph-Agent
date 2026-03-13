from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from fin_insight_graph_agent.ingestion.document_normalizer import NormalizedDocument

TEST_DATABASE_URL = os.getenv(
    "FIGA_TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/fin_insight",
)


@pytest.fixture()
def db_engine() -> Engine:
    engine = create_engine(TEST_DATABASE_URL, future=True)
    with engine.begin() as connection:
        connection.execute(text("drop schema public cascade"))
        connection.execute(text("create schema public"))

    alembic_config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(alembic_config, "head")

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def sample_document() -> NormalizedDocument:
    sample_path = Path("D:/myAgent/.worktrees/fin-insight-v1/tests/fixtures/filings/sample_10k.txt")
    content = sample_path.read_text(encoding="utf-8")
    return NormalizedDocument(
        document_id="doc-sample-10k",
        source_uri=str(sample_path),
        source_type="filing",
        ticker_tags=["NVDA"],
        publication_date="2026-03-13",
        language="en",
        title="Sample 10-K",
        text=content,
        batch_id="batch-20260313",
        version=1,
    )