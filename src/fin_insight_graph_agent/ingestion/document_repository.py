from __future__ import annotations

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