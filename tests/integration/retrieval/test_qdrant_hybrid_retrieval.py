from uuid import uuid4

from fin_insight_graph_agent.retrieval.embeddings import SimpleDenseEmbedder
from fin_insight_graph_agent.retrieval.index_chunks import ChunkIndexRecord, QdrantChunkIndexer
from fin_insight_graph_agent.retrieval.qdrant_client import build_qdrant_client
from fin_insight_graph_agent.retrieval.sparse_encoder import SimpleSparseEncoder
from fin_insight_graph_agent.retrieval.text_retriever import TextRetriever


def test_qdrant_hybrid_retrieval_returns_ranked_evidence():
    collection_name = f"test_chunks_{uuid4().hex[:8]}"
    client = build_qdrant_client()
    dense_embedder = SimpleDenseEmbedder()
    sparse_encoder = SimpleSparseEncoder()
    indexer = QdrantChunkIndexer(client, dense_embedder, sparse_encoder)

    records = [
        ChunkIndexRecord(
            chunk_id="chunk-nvda",
            doc_id="doc-nvda",
            content="NVIDIA disclosed supply constraints at advanced packaging partners.",
            source_type="filing",
            ticker="NVDA",
            publish_date="2026-03-13",
            batch_id="batch-20260313",
            entity_refs=["company:nvda"],
            time_refs=["2026-03-13"],
            market_refs=["ticker:NVDA"],
        ),
        ChunkIndexRecord(
            chunk_id="chunk-amd",
            doc_id="doc-amd",
            content="AMD highlighted data center demand and improved lead times.",
            source_type="filing",
            ticker="AMD",
            publish_date="2026-03-13",
            batch_id="batch-20260313",
            entity_refs=["company:amd"],
            time_refs=["2026-03-13"],
            market_refs=["ticker:AMD"],
        ),
    ]

    indexer.recreate_collection(collection_name)
    indexer.index(collection_name, records)

    retriever = TextRetriever(client, collection_name=collection_name)
    results = retriever.search(
        "Which company reported supply constraints?",
        batch_id="batch-20260313",
        limit=2,
    )

    assert results[0].citation_payload["chunk_id"] == "chunk-nvda"
    assert results[0].retrieval_path == "qdrant.hybrid"