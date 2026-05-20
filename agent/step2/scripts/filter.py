"""STEP 2 filtering by abstract relevance, publication year, and venue quartile."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path
from typing import Iterable


STEP2_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = STEP2_DIR.parents[1]

DEFAULT_INPUT = PROJECT_DIR / "agent" / "step1" / "data" / "raw" / "raw_papers.csv"
DEFAULT_QUARTILES = STEP2_DIR / "data" / "interim" / "venue_quartile_template.csv"
DEFAULT_ABSTRACT_YEAR = STEP2_DIR / "data" / "interim" / "abstract_year_filtered.csv"
DEFAULT_TEMPLATE = STEP2_DIR / "data" / "interim" / "venue_quartile_template.csv"
DEFAULT_NEEDS_QUARTILE = STEP2_DIR / "data" / "interim" / "needs_quartile_review.csv"
DEFAULT_FINAL = STEP2_DIR / "data" / "processed" / "final_q1_q2_papers.csv"
DEFAULT_REJECTED = STEP2_DIR / "data" / "processed" / "rejected_papers.csv"

OUTPUT_COLUMNS = [
    "decision",
    "reject_reason",
    "relevance_score",
    "matched_terms",
    "quartile",
    "title",
    "abstract",
    "year",
    "authors",
    "venue",
    "citations",
    "doi",
    "query_source",
    "pdf_url",
    "source_api",
    "openalex_id",
    "concepts",
]

POSITIVE_PATTERNS = {
    "uav_drone": [
        r"\buav\b",
        r"\buavs\b",
        r"\bdrone\b",
        r"\bdrones\b",
        r"\baerial\b",
        r"unmanned aerial",
        r"remote sensing",
    ],
    "edge_deployment": [
        r"\bedge\b",
        r"edge ai",
        r"edge computing",
        r"embedded",
        r"on-device",
        r"on device",
        r"real-time",
        r"realtime",
        r"low-power",
        r"low power",
        r"jetson",
        r"raspberry pi",
        r"esp32",
        r"stm32",
        r"microcontroller",
        r"\bmcu\b",
        r"tinyml",
    ],
    "lightweight_model": [
        r"lightweight",
        r"efficient cnn",
        r"compact neural",
        r"mobilenet",
        r"efficientnet",
        r"ghostnet",
        r"tinyvit",
        r"mcunet",
        r"yolo",
        r"yolov[0-9]",
        r"nanodet",
        r"shufflenet",
        r"squeezenet",
    ],
    "optimization": [
        r"quantization",
        r"quantized",
        r"pruning",
        r"knowledge distillation",
        r"distillation",
        r"compression",
        r"compressed",
        r"low-bit",
        r"low bit",
        r"neural architecture search",
        r"\bnas\b",
    ],
    "vision_task": [
        r"object detection",
        r"target detection",
        r"tracking",
        r"classification",
        r"segmentation",
        r"surveillance",
        r"monitoring",
        r"agriculture",
        r"wildfire",
        r"disaster",
    ],
}

NEGATIVE_PATTERNS = [
    r"routing protocol",
    r"communication protocol",
    r"path planning",
    r"trajectory planning",
    r"flight control",
    r"formation control",
    r"swarm",
    r"resource allocation",
    r"\bnoma\b",
    r"blockchain",
    r"wireless sensor network",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Filter STEP 1 papers for STEP 2.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--quartiles", type=Path, default=DEFAULT_QUARTILES)
    parser.add_argument("--abstract-year-output", type=Path, default=DEFAULT_ABSTRACT_YEAR)
    parser.add_argument("--template-output", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--needs-quartile-output", type=Path, default=DEFAULT_NEEDS_QUARTILE)
    parser.add_argument("--final-output", type=Path, default=DEFAULT_FINAL)
    parser.add_argument("--rejected-output", type=Path, default=DEFAULT_REJECTED)
    parser.add_argument("--min-year", type=int, default=2020)
    parser.add_argument("--max-year", type=int, default=2026)
    parser.add_argument("--min-score", type=int, default=5)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_venue(venue: str) -> str:
    normalized = venue.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def load_quartiles(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    rows = read_csv(path)
    quartiles: dict[str, str] = {}
    for row in rows:
        venue = normalize_venue(row.get("venue", ""))
        quartile = row.get("quartile", "").upper().strip()
        if venue and quartile:
            quartiles[venue] = quartile
    return quartiles


def find_matches(text: str, patterns: Iterable[str]) -> list[str]:
    matches = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matches.append(pattern.replace(r"\b", "").replace("\\", ""))
    return matches


def score_relevance(row: dict[str, str]) -> tuple[int, list[str], list[str]]:
    haystack = " ".join(
        [
            row.get("title", ""),
            row.get("abstract", ""),
            row.get("concepts", ""),
            row.get("query_source", ""),
        ]
    ).lower()

    matched_terms: list[str] = []
    matched_groups: list[str] = []
    score = 0

    weights = {
        "uav_drone": 3,
        "edge_deployment": 3,
        "lightweight_model": 2,
        "optimization": 2,
        "vision_task": 1,
    }

    for group, patterns in POSITIVE_PATTERNS.items():
        matches = find_matches(haystack, patterns)
        if matches:
            matched_groups.append(group)
            matched_terms.extend(matches)
            score += weights[group]

    negative_matches = find_matches(haystack, NEGATIVE_PATTERNS)
    if negative_matches:
        matched_terms.extend(f"negative:{match}" for match in negative_matches)
        score -= 3

    return score, matched_groups, sorted(set(matched_terms))


def year_in_range(row: dict[str, str], min_year: int, max_year: int) -> bool:
    try:
        year = int(row.get("year", ""))
    except ValueError:
        return False
    return min_year <= year <= max_year


def decision_for(row: dict[str, str], min_year: int, max_year: int, min_score: int) -> dict[str, str]:
    score, groups, terms = score_relevance(row)
    abstract = row.get("abstract", "").strip()

    if not abstract:
        decision = "reject"
        reason = "missing_abstract"
    elif not year_in_range(row, min_year, max_year):
        decision = "reject"
        reason = f"year_outside_{min_year}_{max_year}"
    elif score < min_score:
        decision = "reject"
        reason = "low_abstract_relevance"
    elif "uav_drone" not in groups:
        decision = "reject"
        reason = "missing_uav_or_aerial_context"
    elif not ({"edge_deployment", "lightweight_model", "optimization"} & set(groups)):
        decision = "reject"
        reason = "missing_edge_lightweight_or_optimization_context"
    else:
        decision = "keep"
        reason = ""

    return {
        **row,
        "decision": decision,
        "reject_reason": reason,
        "relevance_score": str(score),
        "matched_terms": "; ".join(terms),
    }


def build_venue_template(rows: list[dict[str, str]], quartiles: dict[str, str]) -> list[dict[str, str]]:
    counts = Counter(row.get("venue", "").strip() for row in rows)
    template = []
    for venue, count in counts.most_common():
        if not venue:
            continue
        template.append(
            {
                "venue": venue,
                "paper_count": str(count),
                "quartile": quartiles.get(normalize_venue(venue), ""),
                "source": "",
                "notes": "",
            }
        )
    return template


def main() -> None:
    args = parse_args()
    papers = read_csv(args.input)
    quartiles = load_quartiles(args.quartiles)

    reviewed = [
        decision_for(row, args.min_year, args.max_year, args.min_score)
        for row in papers
    ]
    abstract_year_kept = [row for row in reviewed if row["decision"] == "keep"]

    for row in reviewed:
        row["quartile"] = quartiles.get(normalize_venue(row.get("venue", "")), "")

    final_rows = [
        row for row in reviewed
        if row["decision"] == "keep" and row["quartile"].upper() in {"Q1", "Q2"}
    ]
    needs_quartile_rows = [
        row for row in reviewed
        if row["decision"] == "keep" and not row["quartile"].strip()
    ]
    rejected_rows = [
        row for row in reviewed
        if row["decision"] != "keep" or row["quartile"].upper() in {"Q3", "Q4"}
    ]
    template_rows = build_venue_template(abstract_year_kept, quartiles)

    write_csv(args.abstract_year_output, abstract_year_kept, OUTPUT_COLUMNS)
    write_csv(args.template_output, template_rows, ["venue", "paper_count", "quartile", "source", "notes"])
    write_csv(args.needs_quartile_output, needs_quartile_rows, OUTPUT_COLUMNS)
    write_csv(args.final_output, final_rows, OUTPUT_COLUMNS)
    write_csv(args.rejected_output, rejected_rows, OUTPUT_COLUMNS)

    q1_q2_count = sum(1 for row in abstract_year_kept if row.get("quartile", "").upper() in {"Q1", "Q2"})
    print(f"Input records: {len(papers)}")
    print(f"Kept after abstract/year filtering: {len(abstract_year_kept)}")
    print(f"Venue template rows: {len(template_rows)}")
    print(f"Needs quartile review records: {len(needs_quartile_rows)}")
    print(f"Final Q1/Q2 records: {len(final_rows)}")
    print(f"Known Q1/Q2 among kept papers: {q1_q2_count}")
    print(f"Abstract/year CSV: {args.abstract_year_output}")
    print(f"Quartile template: {args.template_output}")
    print(f"Final CSV: {args.final_output}")


if __name__ == "__main__":
    main()
