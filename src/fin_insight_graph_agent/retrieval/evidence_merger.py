from __future__ import annotations

from fin_insight_graph_agent.common.models import EvidenceBundle


class EvidenceMerger:
    def merge(self, evidence_lists: list[list[EvidenceBundle]]) -> list[EvidenceBundle]:
        merged: dict[tuple[str | None, str | None, str | None], EvidenceBundle] = {}
        for evidence_list in evidence_lists:
            for bundle in evidence_list:
                doc_id = bundle.citation_payload.get("doc_id")
                chunk_id = bundle.citation_payload.get("chunk_id")
                tail_id = bundle.citation_payload.get("event_id")
                if tail_id is None:
                    tail_id = bundle.citation_payload.get("trade_date")
                key = (doc_id, chunk_id, tail_id)
                existing = merged.get(key)
                if existing is None or bundle.score_raw > existing.score_raw:
                    merged[key] = bundle
        return list(merged.values())