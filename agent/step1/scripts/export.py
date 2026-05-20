"""Apply basic rule filtering and export final CSV/XLSX files."""

from __future__ import annotations

import argparse
from pathlib import Path

from utils import basic_rule_filter, read_csv, save_outputs


STEP1_DIR = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export STEP 1 final raw paper database.")
    parser.add_argument(
        "--input",
        type=Path,
        default=STEP1_DIR / "data" / "raw" / "raw_papers_dedup.csv",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=STEP1_DIR / "data" / "raw" / "raw_papers.csv",
    )
    parser.add_argument(
        "--xlsx",
        type=Path,
        default=STEP1_DIR / "data" / "raw" / "raw_papers.xlsx",
    )
    parser.add_argument("--skip-rule-filter", action="store_true")
    parser.add_argument("--no-xlsx", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    papers = read_csv(args.input)
    filtered = papers if args.skip_rule_filter else [
        paper for paper in papers if basic_rule_filter(paper)
    ]
    save_outputs(filtered, args.csv, None if args.no_xlsx else args.xlsx)

    print(f"Input records: {len(papers)}")
    print(f"Exported records: {len(filtered)}")
    print(f"CSV: {args.csv}")
    if not args.no_xlsx:
        print(f"Excel: {args.xlsx}")


if __name__ == "__main__":
    main()
