"""Shared helpers for STEP 1 literature collection."""

from __future__ import annotations

import csv
import html
import re
import zipfile
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from config import FINAL_COLUMNS, REJECT_WORDS


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """Reconstruct OpenAlex abstract text from its inverted index format."""
    if not inverted_index:
        return ""

    positioned_words: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for position in positions:
            positioned_words.append((position, word))

    positioned_words.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positioned_words)


def normalize_title(title: str | None) -> str:
    if not title:
        return ""
    normalized = title.lower().strip()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_title(left), normalize_title(right)).ratio()


def extract_openalex_work(work: dict[str, Any], query: str) -> dict[str, Any]:
    """Normalize one OpenAlex work into the final STEP 1 schema."""
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}

    authors = []
    for authorship in work.get("authorships", []):
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            authors.append(name)

    concepts = []
    for concept in work.get("concepts", []):
        name = concept.get("display_name")
        if name:
            concepts.append(name)

    return {
        "title": work.get("title") or "",
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "year": work.get("publication_year") or "",
        "authors": "; ".join(authors),
        "venue": source.get("display_name") or "",
        "citations": work.get("cited_by_count") or 0,
        "doi": work.get("doi") or "",
        "query_source": query,
        "pdf_url": primary_location.get("pdf_url") or "",
        "source_api": "OpenAlex",
        "openalex_id": work.get("id") or "",
        "concepts": "; ".join(concepts),
    }


def deduplicate_papers(
    papers: list[dict[str, Any]], title_threshold: float = 0.94
) -> list[dict[str, Any]]:
    """Deduplicate papers by DOI first, then high title similarity."""
    seen_dois: set[str] = set()
    kept: list[dict[str, Any]] = []
    kept_titles: list[str] = []

    for paper in papers:
        doi = str(paper.get("doi") or "").lower().strip()
        title = str(paper.get("title") or "").strip()

        if doi:
            if doi in seen_dois:
                continue
            seen_dois.add(doi)

        normalized = normalize_title(title)
        if normalized and any(
            title_similarity(normalized, kept_title) >= title_threshold
            for kept_title in kept_titles
        ):
            continue

        kept.append(paper)
        kept_titles.append(normalized)

    return kept


def basic_rule_filter(paper: dict[str, Any]) -> bool:
    """Keep paper unless it clearly matches reject keywords."""
    haystack = " ".join(
        [
            str(paper.get("title", "")),
            str(paper.get("abstract", "")),
            str(paper.get("concepts", "")),
        ]
    ).lower()
    return not any(word.lower() in haystack for word in REJECT_WORDS)


def ensure_final_columns(paper: dict[str, Any]) -> dict[str, Any]:
    return {column: paper.get(column, "") for column in FINAL_COLUMNS}


def write_csv(papers: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FINAL_COLUMNS)
        writer.writeheader()
        for paper in papers:
            writer.writerow(ensure_final_columns(paper))


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def _xlsx_col_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _sheet_xml(rows: list[list[Any]]) -> str:
    row_xml = []
    for row_idx, row in enumerate(rows, start=1):
        cells = []
        for col_idx, value in enumerate(row, start=1):
            cell_ref = f"{_xlsx_col_name(col_idx)}{row_idx}"
            safe_value = html.escape(str(value), quote=False)
            cells.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{safe_value}</t></is></c>')
        row_xml.append(f'<row r="{row_idx}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_xml)}</sheetData>'
        "</worksheet>"
    )


def write_xlsx(papers: list[dict[str, Any]], path: Path) -> None:
    """Write a simple XLSX workbook with one worksheet using only stdlib."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[list[Any]] = [FINAL_COLUMNS]
    rows.extend([[ensure_final_columns(paper)[column] for column in FINAL_COLUMNS] for paper in papers])

    files = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            "</Types>"
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>"
        ),
        "xl/workbook.xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="raw_papers" sheetId="1" r:id="rId1"/></sheets>'
            "</workbook>"
        ),
        "xl/_rels/workbook.xml.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            "</Relationships>"
        ),
        "xl/worksheets/sheet1.xml": _sheet_xml(rows),
    }

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as workbook:
        for filename, content in files.items():
            workbook.writestr(filename, content)


def save_outputs(
    papers: list[dict[str, Any]],
    csv_path: Path,
    xlsx_path: Path | None = None,
) -> None:
    write_csv(papers, csv_path)
    if xlsx_path:
        write_xlsx(papers, xlsx_path)
