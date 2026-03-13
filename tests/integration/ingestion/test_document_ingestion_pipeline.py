from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from fin_insight_graph_agent.ingestion.chunker import chunk_document
from fin_insight_graph_agent.ingestion.document_loader import load_document
from fin_insight_graph_agent.ingestion.document_normalizer import normalize_document
from fin_insight_graph_agent.ingestion.document_repository import DocumentRepository
from fin_insight_graph_agent.storage.models.document import Chunk, Document


def test_document_ingestion_pipeline_persists_document_and_chunks(db_engine):
    sample_path = Path("D:/myAgent/.worktrees/fin-insight-v1/tests/fixtures/filings/sample_10k.txt")
    raw_document = load_document(sample_path, source_type="filing", ticker="NVDA")
    normalized_document = normalize_document(raw_document, batch_id="batch-20260313")
    chunks = chunk_document(normalized_document, chunk_size=180, overlap=30)

    repository = DocumentRepository(db_engine)
    repository.save_document_with_chunks(normalized_document, chunks)

    with Session(db_engine) as session:
        stored_documents = session.scalars(select(Document)).all()
        stored_chunks = session.scalars(select(Chunk)).all()

    assert len(stored_documents) == 1
    assert len(stored_chunks) >= 2