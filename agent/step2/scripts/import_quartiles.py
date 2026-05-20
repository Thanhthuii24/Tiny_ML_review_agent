"""Import venue quartiles from an external SJR/SCImago-style CSV file."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


STEP2_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = STEP2_DIR / "data" / "interim" / "venue_quartile_template.csv"


TITLE_CANDIDATES = [
    "title",
    "source title",
    "journal title",
    "venue",
    "name",
    "dcterms_title",
]
QUARTILE_CANDIDATES = [
    "sjr best quartile",
    "sjr quartile",
    "quartile",
    "best quartile",
    "categories",
    "dcterms_coverage",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fill STEP 2 venue quartiles from a downloaded SCImago/SJR CSV."
    )
    parser.add_argument("source", type=Path, help="CSV exported from SCImago/SJR or a similar source.")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_TEMPLATE)
    return parser.parse_args()


def normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def normalize_venue(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\b(the|journal|proceedings|transactions)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def read_csv_flexible(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    encodings = ["utf-8-sig", "utf-8", "latin-1"]
    delimiters = [",", ";", "\t"]
    last_error: Exception | None = None

    for encoding in encodings:
        for delimiter in delimiters:
            try:
                with path.open("r", encoding=encoding, newline="") as file:
                    reader = csv.DictReader(file, delimiter=delimiter)
                    rows = list(reader)
                    if reader.fieldnames and len(reader.fieldnames) > 1:
                        return reader.fieldnames, rows
            except Exception as exc:  # pragma: no cover - diagnostic fallback
                last_error = exc

    raise RuntimeError(f"Cannot parse CSV file: {path}") from last_error


def find_column(columns: list[str], candidates: list[str]) -> str:
    normalized = {normalize_header(column): column for column in columns}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]

    for column in columns:
        norm = normalize_header(column)
        if any(candidate in norm for candidate in candidates):
            return column

    return ""


def extract_quartile(value: str) -> str:
    match = re.search(r"\bQ[1-4]\b", value.upper())
    return match.group(0) if match else ""


def build_quartile_lookup(source: Path) -> dict[str, dict[str, str]]:
    columns, rows = read_csv_flexible(source)
    title_col = find_column(columns, TITLE_CANDIDATES)
    quartile_col = find_column(columns, QUARTILE_CANDIDATES)

    if not title_col or not quartile_col:
        raise RuntimeError(
            "Cannot find title/quartile columns. "
            f"Columns found: {', '.join(columns)}"
        )

    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        title = row.get(title_col, "").strip()
        quartile = extract_quartile(row.get(quartile_col, ""))
        if not title or not quartile:
            continue
        lookup[normalize_venue(title)] = {
            "quartile": quartile,
            "source": source.name,
        }
    return lookup


def main() -> None:
    args = parse_args()
    lookup = build_quartile_lookup(args.source)

    with args.template.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        columns = reader.fieldnames or []

    filled = 0
    for row in rows:
        if row.get("quartile", "").strip():
            continue
        match = lookup.get(normalize_venue(row.get("venue", "")))
        if not match:
            continue
        row["quartile"] = match["quartile"]
        if "source" in row:
            row["source"] = match["source"]
        filled += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Quartile source rows: {len(lookup)}")
    print(f"Template rows filled: {filled}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
