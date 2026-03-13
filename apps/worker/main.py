from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fin Insight worker entrypoint")
    parser.add_argument(
        "--job",
        default="ingestion",
        choices=["ingestion", "evaluation"],
        help="Select which worker loop to bootstrap.",
    )
    return parser


def main() -> str:
    args = build_parser().parse_args()
    return f"worker bootstrap ready for {args.job}"


if __name__ == "__main__":
    print(main())