from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from fin_insight_graph_agent.ingestion.chunker import DocumentChunk
from fin_insight_graph_agent.ingestion.document_normalizer import NormalizedDocument
from fin_insight_graph_agent.storage.models.document import Chunk, Document


class DocumentRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save_document_with_chunks(
        self,
        document: NormalizedDocument,
        chunks: list[DocumentChunk],
    ) -> None:
        with Session(self._engine) as session:
            persisted_document = session.get(Document, document.document_id)
            if persisted_document is None:
                session.add(
                    Document(
                        id=document.document_id,
                        source_uri=document.source_uri,
                        document_type=document.source_type,
                        language=document.language,
                        batch_id=document.batch_id,
                        version=document.version,
                    )
                )
            else:
                persisted_document.source_uri = document.source_uri
                persisted_document.document_type = document.source_type
                persisted_document.language = document.language
                persisted_document.batch_id = document.batch_id
                persisted_document.version = document.version

            session.execute(
                delete(Chunk).where(Chunk.document_id == document.document_id)
            )
            session.add_all(
                [
                    Chunk(
                        id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        chunk_text=chunk.chunk_text,
                        start_offset=chunk.start_offset,
                        end_offset=chunk.end_offset,
                        citation_label=chunk.citation_label,
                        batch_id=chunk.batch_id,
                        version=chunk.version,
                    )
                    for chunk in chunks
                ]
            )
            session.commit()