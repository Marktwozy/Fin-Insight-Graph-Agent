from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from fin_insight_graph_agent.common.models import EvidenceBundle
from fin_insight_graph_agent.retrieval.evidence_merger import EvidenceMerger
from fin_insight_graph_agent.retrieval.market_context_retriever import MarketContextRetriever
from fin_insight_graph_agent.retrieval.reranker import BGEReranker
from fin_insight_graph_agent.storage.models.market import MarketDailyBar


def test_multisource_retrieval_flow_merges_and_reranks(db_engine):
    with Session(db_engine) as session:
        session.add(
            MarketDailyBar(
                id="bar-nvda-20260313",
                ticker="NVDA",
                trade_date=date(2026, 3, 13),
                open_price=Decimal("120.10"),
                high_price=Decimal("125.30"),
                low_price=Decimal("119.85"),
                close_price=Decimal("124.90"),
                volume=45210000,
                batch_id="batch-20260313",
                version=1,
            )
        )
        session.commit()

    market_retriever = MarketContextRetriever(db_engine)
    merger = EvidenceMerger()
    reranker = BGEReranker()

    text_bundle = EvidenceBundle(
        evidence_id="text-1",
        source_type="filing",
        content="NVIDIA disclosed supply constraints at advanced packaging partners.",
        score_raw=0.8,
        score_reranked=None,
        entity_refs=["company:nvda"],
        time_refs=["2026-03-13"],
        market_refs=["ticker:NVDA"],
        citation_payload={"doc_id": "doc-1", "chunk_id": "chunk-1"},
        batch_id="batch-20260313",
        retrieval_path="qdrant.hybrid",
    )
    graph_bundle = EvidenceBundle(
        evidence_id="graph-1",
        source_type="graph",
        content="company:nvda is linked to fab maintenance in advanced packaging.",
        score_raw=1.0,
        score_reranked=None,
        entity_refs=["company:nvda"],
        time_refs=["2026-03-13"],
        market_refs=["ticker:NVDA"],
        citation_payload={"entity_id": "company:nvda", "event_id": "event:fab_maintenance"},
        batch_id="batch-20260313",
        retrieval_path="neo4j.neighborhood",
    )

    market_bundles = market_retriever.search(["NVDA"], batch_id="batch-20260313")
    merged = merger.merge([[text_bundle], [graph_bundle], market_bundles])
    ranked = reranker.rank("What evidence supports NVIDIA supply pressure?", merged)

    assert len(merged) == 3
    assert ranked[0].score_reranked is not None
    assert any(bundle.retrieval_path == "postgres.market" for bundle in ranked)