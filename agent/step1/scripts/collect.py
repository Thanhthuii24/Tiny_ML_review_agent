"""Collect raw literature metadata from OpenAlex."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import BASE_QUERIES, generate_expanded_queries
from utils import basic_rule_filter, deduplicate_papers, extract_openalex_work, save_outputs


OPENALEX_WORKS_URL = "https://api.openalex.org/works"
STEP1_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RAW_CSV = STEP1_DIR / "data" / "raw" / "openalex_raw.csv"
DEFAULT_OUTPUT_CSV = STEP1_DIR / "data" / "raw" / "raw_papers.csv"
DEFAULT_OUTPUT_XLSX = STEP1_DIR / "data" / "raw" / "raw_papers.xlsx"


def build_user_agent(email: str | None) -> str:
    if email:
        return f"TinyUAV literature review pipeline; mailto:{email}"
    return "TinyUAV literature review pipeline"


def openalex_get(
    params: dict[str, Any],
    email: str | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    query_string = urlencode(params)
    request = Request(
        f"{OPENALEX_WORKS_URL}?{query_string}",
        headers={"User-Agent": build_user_agent(email)},
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"OpenAlex HTTP error {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Cannot connect to OpenAlex: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError("OpenAlex request timed out") from exc


def fetch_openalex_query(
    query: str,
    per_page: int,
    max_pages: int,
    email: str | None,
    sleep_seconds: float,
    max_retries: int,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []

    for page in range(1, max_pages + 1):
        params: dict[str, Any] = {
            "search": query,
            "per-page": per_page,
            "page": page,
        }
        if email:
            params["mailto"] = email

        data: dict[str, Any] | None = None
        for attempt in range(1, max_retries + 2):
            try:
                data = openalex_get(params, email, timeout_seconds)
                break
            except RuntimeError as exc:
                if attempt > max_retries:
                    print(f"  warning: skipped page {page} for query '{query}': {exc}")
                    data = None
                    break
                wait_seconds = sleep_seconds + attempt
                print(f"  warning: retry {attempt}/{max_retries} after error: {exc}")
                time.sleep(wait_seconds)

        if data is None:
            continue

        results = data.get("results", [])
        if not results:
            break

        papers.extend(extract_openalex_work(work, query) for work in results)
        time.sleep(sleep_seconds)

    return papers


def collect_openalex(
    queries: list[str],
    per_page: int,
    max_pages: int,
    email: str | None,
    sleep_seconds: float,
    max_retries: int,
    timeout_seconds: float,
    raw_csv_path: Path,
) -> list[dict[str, Any]]:
    all_papers: list[dict[str, Any]] = []

    for index, query in enumerate(queries, start=1):
        print(f"[{index}/{len(queries)}] OpenAlex search: {query}")
        query_papers = fetch_openalex_query(
            query=query,
            per_page=per_page,
            max_pages=max_pages,
            email=email,
            sleep_seconds=sleep_seconds,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
        )
        print(f"  collected: {len(query_papers)}")
        all_papers.extend(query_papers)
        save_outputs(all_papers, raw_csv_path)
        print(f"  saved partial raw CSV: {raw_csv_path}")

    return all_papers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="STEP 1 OpenAlex paper collection.")
    parser.add_argument("--email", default=None, help="Email for OpenAlex polite pool.")
    parser.add_argument("--per-page", type=int, default=25, help="Results per API page.")
    parser.add_argument("--max-pages", type=int, default=1, help="Pages per query.")
    parser.add_argument("--sleep", type=float, default=0.2, help="Delay between API calls.")
    parser.add_argument("--max-retries", type=int, default=2, help="Retries per failed API page.")
    parser.add_argument("--timeout", type=float, default=12.0, help="API timeout in seconds.")
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="Custom query. Can be used multiple times. Defaults to configured query list.",
    )
    parser.add_argument(
        "--expanded-queries",
        action="store_true",
        help="Use generated query combinations for broader recall.",
    )
    parser.add_argument(
        "--query-limit",
        type=int,
        default=None,
        help="Limit number of configured/generated queries.",
    )
    parser.add_argument("--raw-csv", type=Path, default=DEFAULT_RAW_CSV)
    parser.add_argument("--csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_OUTPUT_XLSX)
    parser.add_argument("--no-xlsx", action="store_true")
    parser.add_argument("--skip-rule-filter", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.queries:
        queries = args.queries
    elif args.expanded_queries:
        queries = generate_expanded_queries(limit=args.query_limit)
    else:
        queries = BASE_QUERIES[: args.query_limit] if args.query_limit else BASE_QUERIES

    raw_papers = collect_openalex(
        queries=queries,
        per_page=args.per_page,
        max_pages=args.max_pages,
        email=args.email,
        sleep_seconds=args.sleep,
        max_retries=args.max_retries,
        timeout_seconds=args.timeout,
        raw_csv_path=args.raw_csv,
    )
    save_outputs(raw_papers, args.raw_csv)

    deduped = deduplicate_papers(raw_papers)
    filtered = deduped if args.skip_rule_filter else [
        paper for paper in deduped if basic_rule_filter(paper)
    ]
    save_outputs(filtered, args.csv, None if args.no_xlsx else args.xlsx)

    print("")
    print("STEP 1 complete.")
    print(f"Raw API collection: {len(raw_papers)}")
    print(f"After deduplication: {len(deduped)}")
    print(f"After rule filtering: {len(filtered)}")
    print(f"Raw CSV: {args.raw_csv}")
    print(f"Final CSV: {args.csv}")
    if not args.no_xlsx:
        print(f"Final Excel: {args.xlsx}")


if __name__ == "__main__":
    main()
