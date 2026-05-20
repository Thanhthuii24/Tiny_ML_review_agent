"""Screen STEP 2 Q1/Q2 papers into keep/uncertain/reject by abstract relevance."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


STEP3_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = STEP3_DIR.parents[1]

DEFAULT_INPUT = PROJECT_DIR / "agent" / "step2" / "data" / "processed" / "final_q1_q2_papers.csv"
DEFAULT_OUTPUT_DIR = STEP3_DIR / "data" / "processed"


PATTERNS = {
    "strong_uav_context": [
        r"\buav\b",
        r"\buavs\b",
        r"\bdrone\b",
        r"\bdrones\b",
        r"unmanned aerial",
        r"aerial vehicle",
    ],
    "uav_context": [
        r"\buav\b",
        r"\buavs\b",
        r"\bdrone\b",
        r"\bdrones\b",
        r"unmanned aerial",
        r"aerial image",
        r"aerial imagery",
        r"aerial vehicle",
        r"remote sensing",
    ],
    "tinyml_edge": [
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
    "lightweight_model": [
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
        r"yolo(?:v[0-9]+)?",
        r"yolox",
        r"yolov[0-9]",
    ],
    "optimization": [
        r"quantization",
        r"quantized",
        r"pruning",
        r"pruned",
        r"knowledge distillation",
        r"distillation",
        r"model compression",
        r"compressed model",
        r"low-bit",
        r"low bit",
        r"neural architecture search",
        r"\bnas\b",
    ],
    "deployment_evidence": [
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
        r"deployed",
        r"implementation",
        r"hardware",
    ],
    "uav_task": [
        r"object detection",
        r"target detection",
        r"tracking",
        r"segmentation",
        r"classification",
        r"surveillance",
        r"monitoring",
        r"inspection",
        r"agriculture",
        r"crop",
        r"wildfire",
        r"fire detection",
        r"disaster",
        r"search and rescue",
        r"remaining useful life",
        r"battery",
    ],
    "survey_review": [
        r"\bsurvey\b",
        r"\breview\b",
        r"systematic literature",
        r"state of the art",
        r"state-of-the-art",
        r"taxonomy",
    ],
    "negative_scope": [
        r"routing protocol",
        r"communication protocol",
        r"resource allocation",
        r"\bnoma\b",
        r"wireless communication",
        r"semantic communication",
        r"task offloading",
        r"offloading",
        r"mobile edge computing",
        r"\bmec\b",
        r"path planning",
        r"trajectory planning",
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

TAG_PATTERNS = {
    "model_tags": [
        "MobileNet",
        "EfficientNet",
        "GhostNet",
        "ShuffleNet",
        "SqueezeNet",
        "TinyViT",
        "MCUNet",
        "YOLO",
        "YOLOv3",
        "YOLOv4",
        "YOLOv5",
        "YOLOv7",
        "YOLOv8",
        "YOLOX",
        "NanoDet",
    ],
    "optimization_tags": [
        "quantization",
        "pruning",
        "knowledge distillation",
        "distillation",
        "compression",
        "NAS",
        "low-bit",
    ],
    "device_tags": [
        "TinyML",
        "Jetson",
        "Jetson Nano",
        "Raspberry Pi",
        "ESP32",
        "STM32",
        "MCU",
        "microcontroller",
        "embedded",
        "edge",
    ],
    "task_tags": [
        "object detection",
        "target detection",
        "tracking",
        "segmentation",
        "classification",
        "surveillance",
        "monitoring",
        "inspection",
        "agriculture",
        "wildfire",
        "battery",
    ],
}


OUTPUT_COLUMNS = [
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Screen STEP 2 Q1/Q2 papers by abstract.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def match_patterns(text: str, patterns: list[str]) -> list[str]:
    matches = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matches.append(pattern.replace(r"\b", "").replace("\\", ""))
    return sorted(set(matches))


def find_tag_values(text: str, values: list[str]) -> list[str]:
    tags = []
    lower = text.lower()
    for value in values:
        if value.lower() in lower:
            tags.append(value)
    return sorted(set(tags), key=str.lower)


def classify(row: dict[str, str]) -> dict[str, str]:
    text = " ".join(
        [
            row.get("title", ""),
            row.get("abstract", ""),
        ]
    )
    abstract = row.get("abstract", "").strip()

    axes = {
        axis: match_patterns(text, patterns)
        for axis, patterns in PATTERNS.items()
    }
    positive_axes = [
        axis for axis in [
            "strong_uav_context",
            "uav_context",
            "tinyml_edge",
            "lightweight_model",
            "optimization",
            "deployment_evidence",
            "uav_task",
            "survey_review",
        ]
        if axes[axis]
    ]

    has_strong_uav = bool(axes["strong_uav_context"])
    has_uav = bool(axes["uav_context"])
    has_core_method = bool(
        axes["tinyml_edge"]
        or axes["lightweight_model"]
        or axes["optimization"]
        or axes["deployment_evidence"]
    )
    has_strong_deployment = bool(axes["tinyml_edge"] and axes["deployment_evidence"])
    has_model_or_optimization = bool(axes["lightweight_model"] or axes["optimization"])
    has_task = bool(axes["uav_task"])
    has_negative = bool(axes["negative_scope"])
    is_survey = bool(axes["survey_review"])

    if not abstract:
        decision = "reject"
        confidence = 0.98
        reason = "Missing abstract."
    elif has_negative and not (has_strong_uav and has_model_or_optimization and axes["deployment_evidence"]):
        decision = "reject"
        confidence = 0.86
        reason = "Main abstract signals are outside scope such as communication, routing, planning, or security."
    elif has_strong_uav and has_strong_deployment and has_model_or_optimization and has_task:
        decision = "keep"
        confidence = 0.92
        reason = "Abstract clearly links UAV/drone context, edge/TinyML deployment, model method, and UAV task."
    elif has_strong_uav and has_model_or_optimization and axes["deployment_evidence"] and (axes["tinyml_edge"] or has_task):
        decision = "keep"
        confidence = 0.88
        reason = "Abstract links UAV/drone context with lightweight model or optimization and deployment evidence."
    elif is_survey and has_strong_uav and has_core_method:
        decision = "uncertain"
        confidence = 0.66
        reason = "Survey/review appears related, but needs manual check for UAV edge/TinyML focus."
    elif has_uav and has_core_method:
        decision = "uncertain"
        confidence = 0.62
        reason = "Relevant signals exist, but abstract does not clearly connect deployment, model, task, and UAV context."
    elif has_core_method and not has_uav:
        decision = "uncertain"
        confidence = 0.55
        reason = "Edge/lightweight/optimization is present, but UAV or aerial context is unclear."
    else:
        decision = "reject"
        confidence = 0.82
        reason = "Abstract lacks enough evidence for UAV edge deployment or lightweight/TinyML focus."

    evidence_axes = []
    for axis in positive_axes + (["negative_scope"] if has_negative else []):
        evidence_axes.append(f"{axis}: {', '.join(axes[axis])}")

    screened = {
        **row,
        "screening_decision": decision,
        "screening_confidence": f"{confidence:.2f}",
        "screening_reason": reason,
        "evidence_axes": " | ".join(evidence_axes),
        "step2_relevance_score": row.get("relevance_score", ""),
        "step2_matched_terms": row.get("matched_terms", ""),
    }
    for tag_column, values in TAG_PATTERNS.items():
        screened[tag_column] = "; ".join(find_tag_values(text, values))
    return screened


def main() -> None:
    args = parse_args()
    rows = read_csv(args.input)
    screened = [classify(row) for row in rows]

    keep = [row for row in screened if row["screening_decision"] == "keep"]
    uncertain = [row for row in screened if row["screening_decision"] == "uncertain"]
    reject = [row for row in screened if row["screening_decision"] == "reject"]

    write_csv(args.output_dir / "screened_papers.csv", screened)
    write_csv(args.output_dir / "keep_papers.csv", keep)
    write_csv(args.output_dir / "uncertain_papers.csv", uncertain)
    write_csv(args.output_dir / "reject_papers.csv", reject)

    print(f"Input Q1/Q2 records: {len(rows)}")
    print(f"KEEP: {len(keep)}")
    print(f"UNCERTAIN: {len(uncertain)}")
    print(f"REJECT: {len(reject)}")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
