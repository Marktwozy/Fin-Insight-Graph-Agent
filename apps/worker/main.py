from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from fin_insight_graph_agent.ingestion.daily_batch import (
    DailyBatchOrchestrator,
    build_batch_id_for_date,
)
from fin_insight_graph_agent.ingestion.publish_batch import build_quality_gated_batch_publisher
from fin_insight_graph_agent.ingestion.source_sync import (
    CompanySyncTarget,
    build_official_source_sync_job,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fin Insight worker entrypoint")
    parser.add_argument(
        "--job",
        default="ingestion",
        choices=[
            "ingestion",
            "evaluation",
            "source-sync",
            "source-sync-batch",
            "daily-batch",
            "publish-batch",
        ],
        help="Select which worker loop to bootstrap.",
    )
    parser.add_argument("--ticker", default="NVDA")
    parser.add_argument("--cik", default="1045810")
    parser.add_argument("--batch-id", default="")
    parser.add_argument("--batch-date", default="")
    parser.add_argument(
        "--targets-file",
        default="",
        help="Path to a JSON file containing a list of {ticker, cik} targets.",
    )
    parser.add_argument(
        "--skip-publish",
        action="store_true",
        help="Run sync and validation but do not publish the batch.",
    )
    return parser


def main() -> str:
    args = build_parser().parse_args()
    resolved_batch_id = _resolve_batch_id(args.batch_id, args.batch_date)
    if args.job == "source-sync":
        single_summary = build_official_source_sync_job().sync_company(
            cik=args.cik,
            ticker=args.ticker,
            batch_id=resolved_batch_id,
        )
        return (
            "source sync completed "
            f"for {single_summary.ticker} in {single_summary.batch_id}: "
            f"documents={single_summary.document_count}, "
            f"market_bars={single_summary.market_bar_count}, "
            f"indexed_chunks={single_summary.indexed_chunk_count}"
        )
    if args.job == "source-sync-batch":
        targets = _load_targets(args.targets_file)
        batch_summary = build_official_source_sync_job().sync_companies(
            targets=targets,
            batch_id=resolved_batch_id,
        )
        tickers = ",".join(batch_summary.tickers)
        return (
            "source sync batch completed "
            f"for {batch_summary.company_count} companies in {batch_summary.batch_id}: "
            f"tickers={tickers}, documents={batch_summary.document_count}, "
            f"news_documents={batch_summary.news_document_count}, "
            f"market_bars={batch_summary.market_bar_count}, "
            f"indexed_chunks={batch_summary.indexed_chunk_count}"
        )
    if args.job == "daily-batch":
        orchestrator = DailyBatchOrchestrator(
            build_official_source_sync_job(),
            build_quality_gated_batch_publisher(),
        )
        targets = _load_targets(args.targets_file)
        run_summary = orchestrator.run(
            targets=targets,
            batch_id=resolved_batch_id,
            publish_on_pass=not args.skip_publish,
        )
        tickers = ",".join(run_summary.sync_summary.tickers)
        if run_summary.validation.passed and run_summary.published:
            return (
                "daily batch completed and published "
                f"for {resolved_batch_id}: tickers={tickers}, "
                f"documents={run_summary.sync_summary.document_count}, "
                f"news_documents={run_summary.sync_summary.news_document_count}, "
                f"market_bars={run_summary.sync_summary.market_bar_count}"
            )
        if run_summary.validation.passed:
            return (
                "daily batch validated but not published "
                f"for {resolved_batch_id}: tickers={tickers}, "
                f"documents={run_summary.sync_summary.document_count}, "
                f"news_documents={run_summary.sync_summary.news_document_count}, "
                f"market_bars={run_summary.sync_summary.market_bar_count}"
            )
        return (
            "daily batch blocked by quality gate "
            f"for {resolved_batch_id}: tickers={tickers}, "
            f"failures={run_summary.validation.threshold_failures}"
        )
    if args.job == "publish-batch":
        publisher = build_quality_gated_batch_publisher()
        validation = publisher.mark_validated(resolved_batch_id)
        if not validation.passed:
            return (
                f"batch publish blocked for {resolved_batch_id}: "
                f"suite={validation.suite_name} failures={validation.threshold_failures}"
            )
        publisher.publish(resolved_batch_id)
        return (
            f"batch published for {resolved_batch_id}: "
            f"suite={validation.suite_name} metrics={validation.metrics}"
        )
    return f"worker bootstrap ready for {args.job}"


def _load_targets(targets_file: str) -> list[CompanySyncTarget]:
    if not targets_file:
        raise ValueError("--targets-file is required for source-sync-batch and daily-batch")

    payload = json.loads(Path(targets_file).read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("targets file must contain a non-empty JSON array")

    targets: list[CompanySyncTarget] = []
    for item in payload:
        ticker = str(item["ticker"]).strip().upper()
        cik = str(item["cik"]).strip()
        targets.append(CompanySyncTarget(ticker=ticker, cik=cik))
    return targets


def _resolve_batch_id(batch_id: str, batch_date: str) -> str:
    if batch_id:
        return batch_id
    if batch_date:
        return build_batch_id_for_date(date.fromisoformat(batch_date))
    return build_batch_id_for_date(date.today())


if __name__ == "__main__":
    print(main())