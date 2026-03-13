from __future__ import annotations

import argparse

from fin_insight_graph_agent.ingestion.publish_batch import build_quality_gated_batch_publisher
from fin_insight_graph_agent.ingestion.source_sync import build_official_source_sync_job


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fin Insight worker entrypoint")
    parser.add_argument(
        "--job",
        default="ingestion",
        choices=["ingestion", "evaluation", "source-sync", "publish-batch"],
        help="Select which worker loop to bootstrap.",
    )
    parser.add_argument("--ticker", default="NVDA")
    parser.add_argument("--cik", default="1045810")
    parser.add_argument("--batch-id", default="batch-20260313")
    return parser


def main() -> str:
    args = build_parser().parse_args()
    if args.job == "source-sync":
        summary = build_official_source_sync_job().sync_company(
            cik=args.cik,
            ticker=args.ticker,
            batch_id=args.batch_id,
        )
        return (
            "source sync completed "
            f"for {summary.ticker} in {summary.batch_id}: "
            f"documents={summary.document_count}, market_bars={summary.market_bar_count}"
        )
    if args.job == "publish-batch":
        publisher = build_quality_gated_batch_publisher()
        validation = publisher.mark_validated(args.batch_id)
        if not validation.passed:
            return (
                f"batch publish blocked for {args.batch_id}: "
                f"suite={validation.suite_name} failures={validation.threshold_failures}"
            )
        publisher.publish(args.batch_id)
        return (
            f"batch published for {args.batch_id}: "
            f"suite={validation.suite_name} metrics={validation.metrics}"
        )
    return f"worker bootstrap ready for {args.job}"


if __name__ == "__main__":
    print(main())