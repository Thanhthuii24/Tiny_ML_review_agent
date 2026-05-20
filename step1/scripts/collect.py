"""Collect raw paper metadata from OpenAlex for STEP 1."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: requests. Install with: pip install -r step1/requirements.txt"
    ) from exc

from config import BASE_QUERIES
from utils import basic_rule_filter, deduplicate_papers, extract_openalex_work, save_outputs


OPENALEX_WORKS_URL = "https://api.openalex.org/works"
DEFAULT_OUTPUT_CSV = Path("step1/data/raw/raw_papers.csv")
DEFAULT_OUTPUT_XLSX = Path("step1/data/raw/raw_papers.xlsx")
DEFAULT_RAW_OPENALEX_CSV = Path("step1/data/raw/openalex_raw.csv")


def build_headers(email: str | None) -> dict[str, str]:
    if not email:
        return {"User-Agent": "TinyUAV literature review pipeline"}
    return {"User-Agent": f"TinyUAV literature review pipeline; mailto:{email}"}


def fetch_openalex_query(
    query: str,
    per_page: int,
    max_pages: int,
    email: str | None,
    sleep_seconds: float,
) -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []
    headers = build_headers(email)

    for page in range(1, max_pages + 1):
        params = {
            "search": query,
            "per-page": per_page,
            "page": page,
        }
        if email:
            params["mailto"] = email

        response = requests.get(
            OPENALEX_WORKS_URL,
            params=params,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])
        if not results:
            break

        for work in results:
            papers.append(extract_openalex_work(work, query))

        time.sleep(sleep_seconds)

    return papers


def collect_openalex(
    queries: list[str],
    per_page: int,
    max_pages: int,
    email: str | None,
    sleep_seconds: float,
) -> list[dict[str, Any]]:
    all_papers: list[dict[str, Any]] = []

    for idx, query in enumerate(queries, start=1):
        print(f"[{idx}/{len(queries)}] OpenAlex search: {query}")
        query_papers = fetch_openalex_query(
            query=query,
            per_page=per_page,
            max_pages=max_pages,
            email=email,
            sleep_seconds=sleep_seconds,
        )
        print(f"  -> collected {len(query_papers)} records")
        all_papers.extend(query_papers)

    return all_papers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect STEP 1 raw papers from OpenAlex.")
    parser.add_argument("--email", default=None, help="Email for OpenAlex polite pool.")
    parser.add_argument("--per-page", type=int, default=25, help="OpenAlex results per page.")
    parser.add_argument("--max-pages", type=int, default=1, help="Pages per query.")
    parser.add_argument("--sleep", type=float, default=0.2, help="Delay between API requests.")
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="Custom query. Can be passed multiple times. Defaults to config.BASE_QUERIES.",
    )
    parser.add_argument("--raw-csv", type=Path, default=DEFAULT_RAW_OPENALEX_CSV)
    parser.add_argument("--csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_OUTPUT_XLSX)
    parser.add_argument(
        "--no-xlsx",
        action="store_true",
        help="Only export CSV. Useful if openpyxl is not installed.",
    )
    parser.add_argument(
        "--skip-rule-filter",
        action="store_true",
        help="Keep records that match coarse reject keywords.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    queries = args.queries or BASE_QUERIES

    raw_papers = collect_openalex(
        queries=queries,
        per_page=args.per_page,
        max_pages=args.max_pages,
        email=args.email,
        sleep_seconds=args.sleep,
    )
    save_outputs(raw_papers, args.raw_csv, None)

    deduped = deduplicate_papers(raw_papers)
    if args.skip_rule_filter:
        filtered = deduped
    else:
        filtered = [paper for paper in deduped if basic_rule_filter(paper)]

    save_outputs(filtered, args.csv, None if args.no_xlsx else args.xlsx)

    print("\nDone.")
    print(f"Raw records: {len(raw_papers)}")
    print(f"After deduplication: {len(deduped)}")
    print(f"After rule filtering: {len(filtered)}")
    print(f"CSV: {args.csv}")
    if not args.no_xlsx:
        print(f"Excel: {args.xlsx}")


if __name__ == "__main__":
    main()
