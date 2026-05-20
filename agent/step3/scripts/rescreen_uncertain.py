"""Semi-conservative rescreening for STEP 3 uncertain papers."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


STEP3_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = STEP3_DIR / "data" / "processed"

DEFAULT_UNCERTAIN = PROCESSED_DIR / "uncertain_papers.csv"
DEFAULT_KEEP = PROCESSED_DIR / "keep_papers.csv"
DEFAULT_REJECT = PROCESSED_DIR / "reject_papers.csv"

OUTPUT_COLUMNS = [
    "uncertain_decision",
    "uncertain_confidence",
    "uncertain_reason",
    "missing_evidence",
    "screening_decision",
    "screening_confidence",
    "screening_reason",
    "evidence_axes",
    "model_tags",
    "optimization_tags",
    "device_tags",
    "task_tags",
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
    "step2_relevance_score",
    "step2_matched_terms",
]

FINAL_COLUMNS = [
    "final_decision",
    "final_source",
    "final_confidence",
    "final_reason",
    *[column for column in OUTPUT_COLUMNS if column not in {
        "uncertain_decision",
        "uncertain_confidence",
        "uncertain_reason",
    }],
]


PATTERNS = {
    "strong_uav": [
        r"\buav\b",
        r"\buavs\b",
        r"\bdrone\b",
        r"\bdrones\b",
        r"unmanned aerial",
        r"aerial vehicle",
        r"quadcopter",
    ],
    "weak_aerial": [
        r"aerial image",
        r"aerial imagery",
        r"remote sensing",
        r"satellite",
    ],
    "edge_tinyml": [
        r"tinyml",
        r"edge ai",
        r"edge computing",
        r"\bedge\b",
        r"embedded",
        r"on-device",
        r"on device",
        r"microcontroller",
        r"\bmcu\b",
        r"jetson",
        r"raspberry pi",
        r"esp32",
        r"stm32",
        r"low-power",
        r"low power",
    ],
    "model": [
        r"lightweight",
        r"compact neural",
        r"efficient cnn",
        r"mobilenet",
        r"efficientnet",
        r"ghostnet",
        r"shufflenet",
        r"squeezenet",
        r"tinyvit",
        r"mcunet",
        r"nanodet",
        r"\byolo\b",
        r"yolov[0-9]",
        r"yolox",
        r"vision transformer",
    ],
    "optimization": [
        r"quantization",
        r"quantized",
        r"pruning",
        r"pruned",
        r"knowledge distillation",
        r"distillation",
        r"compression",
        r"low-bit",
        r"low bit",
        r"neural architecture search",
        r"\bnas\b",
    ],
    "deployment": [
        r"real-time",
        r"realtime",
        r"inference latency",
        r"\blatency\b",
        r"\bfps\b",
        r"frames per second",
        r"memory",
        r"\bram\b",
        r"\bflash\b",
        r"power consumption",
        r"energy consumption",
        r"energy-efficient",
        r"hardware",
        r"deployed",
        r"implementation",
    ],
    "task": [
        r"object detection",
        r"target detection",
        r"human detection",
        r"tracking",
        r"segmentation",
        r"classification",
        r"inspection",
        r"monitoring",
        r"surveillance",
        r"smart farming",
        r"agriculture",
        r"crop",
        r"wildfire",
        r"fire detection",
        r"search and rescue",
        r"disaster",
        r"landing",
        r"navigation",
        r"battery",
        r"remaining useful life",
    ],
    "survey": [
        r"\bsurvey\b",
        r"\breview\b",
        r"systematic literature",
        r"state of the art",
        r"state-of-the-art",
        r"taxonomy",
    ],
    "negative": [
        r"semantic communication",
        r"wireless communication",
        r"communication protocol",
        r"routing",
        r"resource allocation",
        r"\bnoma\b",
        r"task offloading",
        r"offloading",
        r"mobile edge computing",
        r"\bmec\b",
        r"trajectory",
        r"path planning",
        r"flight control",
        r"formation control",
        r"swarm",
        r"blockchain",
        r"authentication",
        r"encryption",
        r"6g",
        r"space-air-ground",
        r"space air ground",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rescreen STEP 3 uncertain papers.")
    parser.add_argument("--uncertain", type=Path, default=DEFAULT_UNCERTAIN)
    parser.add_argument("--keep", type=Path, default=DEFAULT_KEEP)
    parser.add_argument("--reject", type=Path, default=DEFAULT_REJECT)
    parser.add_argument("--output-dir", type=Path, default=PROCESSED_DIR)
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


def has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def matched_groups(text: str) -> dict[str, bool]:
    return {group: has_any(text, patterns) for group, patterns in PATTERNS.items()}


def missing_evidence(groups: dict[str, bool]) -> str:
    missing = []
    if not groups["strong_uav"]:
        missing.append("explicit UAV/drone context")
    if not groups["edge_tinyml"]:
        missing.append("edge/TinyML/embedded evidence")
    if not groups["model"] and not groups["optimization"]:
        missing.append("lightweight model or optimization method")
    if not groups["deployment"]:
        missing.append("deployment metrics or hardware evidence")
    if not groups["task"]:
        missing.append("UAV application task")
    return "; ".join(missing) if missing else "none"


def rescreen(row: dict[str, str]) -> dict[str, str]:
    text = " ".join([row.get("title", ""), row.get("abstract", "")])
    groups = matched_groups(text)

    positive_count = sum(
        1
        for group in ["strong_uav", "edge_tinyml", "model", "optimization", "deployment", "task"]
        if groups[group]
    )

    if groups["negative"] and not (
        groups["strong_uav"]
        and groups["edge_tinyml"]
        and (groups["model"] or groups["optimization"])
        and groups["task"]
    ):
        decision = "demote_to_reject"
        confidence = 0.86
        reason = "Abstract mainly points to communication, offloading, planning, control, or security rather than UAV edge AI deployment."
    elif groups["strong_uav"] and groups["edge_tinyml"] and groups["deployment"] and groups["task"]:
        decision = "promote_to_keep"
        confidence = 0.82
        reason = "Abstract explicitly combines UAV/drone context, edge/TinyML evidence, deployment evidence, and an application task."
    elif groups["strong_uav"] and groups["edge_tinyml"] and (groups["model"] or groups["optimization"]) and positive_count >= 4:
        decision = "promote_to_keep"
        confidence = 0.80
        reason = "Abstract has explicit UAV/drone context plus edge/TinyML and model or optimization evidence."
    elif groups["strong_uav"] and groups["model"] and groups["task"] and groups["deployment"]:
        decision = "promote_to_keep"
        confidence = 0.78
        reason = "Abstract has explicit UAV/drone context, model evidence, task, and deployment/efficiency evidence."
    elif groups["weak_aerial"] and not groups["strong_uav"] and not groups["edge_tinyml"]:
        decision = "demote_to_reject"
        confidence = 0.84
        reason = "Remote sensing or aerial imagery appears without explicit UAV edge/TinyML deployment."
    elif groups["survey"] and not (groups["strong_uav"] and groups["edge_tinyml"]):
        decision = "demote_to_reject"
        confidence = 0.80
        reason = "General survey/review without clear UAV edge/TinyML focus."
    else:
        decision = "remain_uncertain"
        confidence = 0.58
        reason = "Abstract is partially relevant but lacks enough evidence for a confident keep/reject decision."

    return {
        **row,
        "uncertain_decision": decision,
        "uncertain_confidence": f"{confidence:.2f}",
        "uncertain_reason": reason,
        "missing_evidence": missing_evidence(groups),
    }


def final_from_existing(row: dict[str, str], decision: str, source: str) -> dict[str, str]:
    return {
        **row,
        "final_decision": decision,
        "final_source": source,
        "final_confidence": row.get("screening_confidence", ""),
        "final_reason": row.get("screening_reason", ""),
        "missing_evidence": row.get("missing_evidence", ""),
    }


def final_from_rescreened(row: dict[str, str], decision: str) -> dict[str, str]:
    return {
        **row,
        "final_decision": decision,
        "final_source": "uncertain_rescreen",
        "final_confidence": row.get("uncertain_confidence", ""),
        "final_reason": row.get("uncertain_reason", ""),
    }


def main() -> None:
    args = parse_args()
    uncertain_rows = [rescreen(row) for row in read_csv(args.uncertain)]
    original_keep = read_csv(args.keep)
    original_reject = read_csv(args.reject)

    promote = [row for row in uncertain_rows if row["uncertain_decision"] == "promote_to_keep"]
    remain = [row for row in uncertain_rows if row["uncertain_decision"] == "remain_uncertain"]
    demote = [row for row in uncertain_rows if row["uncertain_decision"] == "demote_to_reject"]

    final_keep = (
        [final_from_existing(row, "keep", "initial_screen") for row in original_keep]
        + [final_from_rescreened(row, "keep") for row in promote]
    )
    final_uncertain = [final_from_rescreened(row, "uncertain") for row in remain]
    final_reject = (
        [final_from_existing(row, "reject", "initial_screen") for row in original_reject]
        + [final_from_rescreened(row, "reject") for row in demote]
    )

    write_csv(args.output_dir / "uncertain_rescreened.csv", uncertain_rows, OUTPUT_COLUMNS)
    write_csv(args.output_dir / "uncertain_promote_to_keep.csv", promote, OUTPUT_COLUMNS)
    write_csv(args.output_dir / "uncertain_remain_uncertain.csv", remain, OUTPUT_COLUMNS)
    write_csv(args.output_dir / "uncertain_demote_to_reject.csv", demote, OUTPUT_COLUMNS)
    write_csv(args.output_dir / "final_keep_papers.csv", final_keep, FINAL_COLUMNS)
    write_csv(args.output_dir / "final_uncertain_papers.csv", final_uncertain, FINAL_COLUMNS)
    write_csv(args.output_dir / "final_reject_papers.csv", final_reject, FINAL_COLUMNS)

    print(f"Input uncertain records: {len(uncertain_rows)}")
    print(f"Promote to KEEP: {len(promote)}")
    print(f"Remain UNCERTAIN: {len(remain)}")
    print(f"Demote to REJECT: {len(demote)}")
    print(f"Final KEEP: {len(final_keep)}")
    print(f"Final UNCERTAIN: {len(final_uncertain)}")
    print(f"Final REJECT: {len(final_reject)}")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
