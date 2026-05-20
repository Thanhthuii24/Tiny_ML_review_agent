"""Deduplicate an existing STEP 1 CSV file."""

from __future__ import annotations

import argparse
from pathlib import Path

from utils import deduplicate_papers, read_csv, write_csv


STEP1_DIR = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deduplicate STEP 1 paper CSV.")
    parser.add_argument(
        "--input",
        type=Path,
        default=STEP1_DIR / "data" / "raw" / "openalex_raw.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=STEP1_DIR / "data" / "raw" / "raw_papers_dedup.csv",
    )
    parser.add_argument("--title-threshold", type=float, default=0.94)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    papers = read_csv(args.input)
    deduped = deduplicate_papers(papers, title_threshold=args.title_threshold)
    write_csv(deduped, args.output)

    print(f"Input records: {len(papers)}")
    print(f"Deduplicated records: {len(deduped)}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
