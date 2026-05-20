"""Deduplicate a STEP 1 paper CSV by DOI and title similarity."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: pandas. Install with: pip install -r step1/requirements.txt"
    ) from exc

from utils import deduplicate_papers, ensure_final_columns


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deduplicate raw paper CSV.")
    parser.add_argument("--input", type=Path, default=Path("step1/data/raw/openalex_raw.csv"))
    parser.add_argument("--output", type=Path, default=Path("step1/data/raw/raw_papers_dedup.csv"))
    parser.add_argument("--title-threshold", type=float, default=0.94)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input)
    papers = df.fillna("").to_dict(orient="records")
    deduped = deduplicate_papers(papers, title_threshold=args.title_threshold)

    output_df = ensure_final_columns(pd.DataFrame(deduped))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(args.output, index=False, encoding="utf-8-sig")

    print(f"Input records: {len(papers)}")
    print(f"Deduplicated records: {len(deduped)}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
