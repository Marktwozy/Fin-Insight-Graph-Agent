from fin_insight_graph_agent.ingestion.chunker import chunk_document


def test_chunk_document_preserves_offsets_and_parent_id(sample_document):
    chunks = chunk_document(sample_document, chunk_size=200, overlap=40)
    assert chunks[0].document_id == sample_document.document_id
    assert chunks[0].start_offset == 0
    assert chunks[1].start_offset < chunks[1].end_offset