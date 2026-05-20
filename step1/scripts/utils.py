"""Shared helpers for paper collection, normalization, and filtering."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: pandas. Install with: pip install -r step1/requirements.txt"
    ) from exc

from config import FINAL_COLUMNS, REJECT_WORDS


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """Reconstruct OpenAlex abstract text from its inverted index."""
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
    title = title.lower().strip()
    title = re.sub(r"[^a-z0-9\s]", " ", title)
    title = re.sub(r"\s+", " ", title)
    return title


def title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_title(left), normalize_title(right)).ratio()


def extract_openalex_work(work: dict[str, Any], query: str) -> dict[str, Any]:
    """Convert an OpenAlex work object into the unified paper schema."""
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


def basic_rule_filter(paper: dict[str, Any]) -> bool:
    """Return True when a paper should be kept after coarse rule filtering."""
    haystack = " ".join(
        [
            str(paper.get("title", "")),
            str(paper.get("abstract", "")),
            str(paper.get("concepts", "")),
        ]
    ).lower()

    return not any(word.lower() in haystack for word in REJECT_WORDS)


def deduplicate_papers(
    papers: list[dict[str, Any]], title_threshold: float = 0.94
) -> list[dict[str, Any]]:
    """Deduplicate by DOI first, then by high title similarity."""
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


def ensure_final_columns(df: pd.DataFrame) -> pd.DataFrame:
    for column in FINAL_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df[FINAL_COLUMNS]


def save_outputs(papers: list[dict[str, Any]], csv_path: Path, xlsx_path: Path | None) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df = ensure_final_columns(pd.DataFrame(papers))
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    if xlsx_path:
        xlsx_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(xlsx_path, index=False)
