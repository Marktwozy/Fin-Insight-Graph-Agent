from datetime import date
from decimal import Decimal
from uuid import uuid4

from fin_insight_graph_agent.ingestion.market_loader import DailyBarRecord
from fin_insight_graph_agent.ingestion.source_sync import OfficialSourceSyncJob
from fin_insight_graph_agent.retrieval.embeddings import OpenAICompatibleDenseEmbedder
from fin_insight_graph_agent.retrieval.index_chunks import QdrantChunkIndexer
from fin_insight_graph_agent.retrieval.qdrant_client import build_qdrant_client
from fin_insight_graph_agent.retrieval.text_retriever import TextRetriever


class FakeTransport:
    def post_json(self, url, *, payload, headers=None):
        text = payload['input']
        if 'supply constraints' in text.lower():
            return {'data': [{'embedding': [1.0, 0.0, 0.0]}]}
        if 'which filing mentions supply constraints' in text.lower():
            return {'data': [{'embedding': [1.0, 0.0, 0.0]}]}
        return {'data': [{'embedding': [0.0, 1.0, 0.0]}]}


class FakeSecClient:
    def fetch_submissions(self, cik):
        return {'cik': cik, 'form': ['10-K']}

    def fetch_company_facts(self, cik):
        return {'cik': cik, 'summary': 'NVIDIA disclosed supply constraints in packaging.'}


class FakeAlphaVantageClient:
    def fetch_daily_adjusted(self, symbol, outputsize='compact'):
        return [
            DailyBarRecord(
                ticker=symbol,
                trade_date=date(2026, 3, 13),
                open_price=Decimal('118.00'),
                high_price=Decimal('120.00'),
                low_price=Decimal('117.50'),
                close_price=Decimal('119.50'),
                volume=1200000,
            )
        ]

    def fetch_news_sentiment(self, tickers, limit=20):
        return []


class FakeDocumentRepository:
    def save_document_with_chunks(self, document, chunks):
        return None


class FakeMarketRepository:
    def upsert_daily_bars(self, bars, batch_id):
        return None


class FakeBatchRepository:
    def create_batch(self, batch_id, status):
        return {'batch_id': batch_id, 'status': status}


def test_source_sync_indexes_chunks_with_openai_compatible_embeddings_into_qdrant():
    collection_name = f'test_chunks_{uuid4().hex[:8]}'
    embedder = OpenAICompatibleDenseEmbedder(
        base_url='https://models.example/v1',
        model='text-embedding-3-small',
        dimensions=3,
        transport=FakeTransport(),
    )
    client = build_qdrant_client(dense_embedder=embedder)
    indexer = QdrantChunkIndexer(client)
    job = OfficialSourceSyncJob(
        sec_client=FakeSecClient(),
        alpha_vantage_client=FakeAlphaVantageClient(),
        document_repository=FakeDocumentRepository(),
        market_repository=FakeMarketRepository(),
        batch_repository=FakeBatchRepository(),
        chunk_indexer=indexer,
        qdrant_collection_name=collection_name,
    )

    summary = job.sync_company(cik='1045810', ticker='NVDA', batch_id='batch-20260313')
    retriever = TextRetriever(client, collection_name=collection_name)
    results = retriever.search(
        'Which filing mentions supply constraints?',
        batch_id='batch-20260313',
        limit=3,
    )

    assert summary.indexed_chunk_count > 0
    assert results
    assert 'supply constraints' in results[0].content.lower()