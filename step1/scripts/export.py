"""Apply coarse rule filtering and export CSV/XLSX for STEP 1."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: pandas. Install with: pip install -r step1/requirements.txt"
    ) from exc

from utils import basic_rule_filter, ensure_final_columns


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export final STEP 1 raw paper files.")
    parser.add_argument("--input", type=Path, default=Path("step1/data/raw/raw_papers_dedup.csv"))
    parser.add_argument("--csv", type=Path, default=Path("step1/data/raw/raw_papers.csv"))
    parser.add_argument("--xlsx", type=Path, default=Path("step1/data/raw/raw_papers.xlsx"))
    parser.add_argument("--skip-rule-filter", action="store_true")
    parser.add_argument("--no-xlsx", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input).fillna("")
    papers = df.to_dict(orient="records")

    if args.skip_rule_filter:
        filtered = papers
    else:
        filtered = [paper for paper in papers if basic_rule_filter(paper)]

    output_df = ensure_final_columns(pd.DataFrame(filtered))
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(args.csv, index=False, encoding="utf-8-sig")

    if not args.no_xlsx:
        args.xlsx.parent.mkdir(parents=True, exist_ok=True)
        output_df.to_excel(args.xlsx, index=False)

    print(f"Input records: {len(papers)}")
    print(f"Exported records: {len(filtered)}")
    print(f"CSV: {args.csv}")
    if not args.no_xlsx:
        print(f"Excel: {args.xlsx}")


if __name__ == "__main__":
    main()
