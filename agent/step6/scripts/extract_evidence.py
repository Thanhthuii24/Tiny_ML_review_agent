"""Extract detailed evidence fields from STEP 5 core papers."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


STEP6_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = STEP6_DIR.parents[1]
DEFAULT_INPUT = PROJECT_DIR / "agent" / "step5" / "data" / "processed" / "core_papers.csv"
DEFAULT_OUTPUT_DIR = STEP6_DIR / "data" / "processed"


ACCURACY_METRICS = {"accuracy", "mAP", "precision", "recall", "F1"}
DEPLOYMENT_METRICS = {
    "FPS",
    "latency",
    "inference latency",
    "memory",
    "RAM",
    "flash",
    "power",
    "energy",
    "real-time",
    "realtime",
}
HARD_DEPLOYMENT_METRICS = DEPLOYMENT_METRICS - {"real-time", "realtime"}
MCU_HARDWARE = {"ESP32", "STM32", "Arduino", "MCU", "microcontroller"}
EDGE_GPU_HARDWARE = {"Jetson Nano", "Jetson Xavier", "Jetson", "GPU", "FPGA"}


DATASET_PATTERNS = [
    r"\bVisDrone\b",
    r"\bUAVDT\b",
    r"\bDOTA\b",
    r"\bDIOR\b",
    r"\bCOCO\b",
    r"\bImageNet\b",
    r"\bPASCAL VOC\b",
    r"\bCIFAR-?10\b",
    r"\bCIFAR-?100\b",
    r"\bFLIR\b",
    r"\bAIDER\b",
    r"\bDroneVehicle\b",
    r"\bUAVid\b",
    r"\bAerial Maritime\b",
    r"\bdataset\b",
]


EVIDENCE_COLUMNS = [
    "paper_id",
    "core_rank",
    "core_score",
    "title",
    "year",
    "venue",
    "quartile",
    "link",
    "research_problem",
    "uav_task",
    "model",
    "optimization",
    "hardware",
    "deployment_setting",
    "dataset",
    "accuracy_metrics",
    "deployment_metrics",
    "reported_tradeoff",
    "main_contribution",
    "limitations_or_missing_info",
    "gap_relevance",
    "evidence_confidence",
    "abstract",
    "doi",
    "pdf_url",
    "openalex_id",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract evidence from STEP 5 core papers.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return reader.fieldnames or [], list(reader)


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def split_values(value: str) -> set[str]:
    return {item.strip() for item in value.split(";") if item.strip()}


def ordered_join(values: set[str]) -> str:
    return "; ".join(sorted(values, key=str.lower)) if values else "not_reported"


def link_for(row: dict[str, str]) -> str:
    return row.get("pdf_url", "").strip() or row.get("doi", "").strip() or row.get("openalex_id", "").strip()


def find_dataset(text: str) -> str:
    found = []
    for pattern in DATASET_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(pattern.replace(r"\b", "").replace("\\", ""))
    if not found:
        return "not_reported"
    if found == ["dataset"]:
        return "dataset_mentioned_name_not_reported"
    return "; ".join(sorted(set(found), key=str.lower))


def research_problem(row: dict[str, str]) -> str:
    title = row.get("title", "").lower()
    tasks = split_values(row.get("uav_task", ""))
    hardware = split_values(row.get("hardware_platform", ""))
    optimizations = split_values(row.get("optimization_method", ""))

    if "survey" in title or "review" in title:
        return "survey_or_review_of_uav_edge_ai_literature"
    if {"fire detection", "wildfire"} & tasks:
        return "real_time_uav_wildfire_or_fire_detection"
    if "object detection" in tasks or "target detection" in tasks:
        return "real_time_uav_object_or_target_detection"
    if "inspection" in tasks or "structural health" in tasks:
        return "uav_infrastructure_inspection_under_edge_constraints"
    if {"agriculture", "smart farming", "crop"} & tasks:
        return "uav_precision_agriculture_or_crop_monitoring"
    if "navigation" in tasks or "landing" in tasks:
        return "uav_navigation_or_landing_with_onboard_ai"
    if "battery" in tasks or "remaining useful life" in tasks:
        return "uav_battery_or_health_estimation_on_edge"
    if hardware or optimizations:
        return "efficient_uav_edge_inference_under_resource_constraints"
    return "uav_edge_ai_application_not_fully_specified"


def deployment_setting(row: dict[str, str], text: str) -> str:
    hardware = split_values(row.get("hardware_platform", ""))
    if re.search(r"\bon-?board\b|onboard|on the uav|on drones?|on uavs?", text, re.I):
        return "onboard_uav"
    if hardware & (MCU_HARDWARE | EDGE_GPU_HARDWARE | {"Raspberry Pi"}):
        return "edge_embedded_hardware"
    if {"edge", "embedded", "TinyML"} & hardware:
        return "edge_general"
    if re.search(r"\bsimulation\b|simulated|algorithm", text, re.I):
        return "simulation_or_algorithmic"
    return "unclear"


def tradeoff(row: dict[str, str], text: str) -> str:
    metrics = split_values(row.get("metrics_evidence", ""))
    has_accuracy = bool(metrics & ACCURACY_METRICS)
    has_deployment = bool(metrics & HARD_DEPLOYMENT_METRICS)
    if re.search(r"trade-?off|balance|accuracy.*latency|latency.*accuracy|accuracy.*power|power.*accuracy", text, re.I):
        return "explicit_tradeoff_reported"
    if has_accuracy and has_deployment:
        return "implicit_accuracy_deployment_tradeoff_available"
    if has_deployment:
        return "deployment_metrics_without_accuracy_tradeoff"
    if has_accuracy:
        return "accuracy_only_no_deployment_tradeoff"
    return "not_reported"


def contribution(row: dict[str, str]) -> str:
    problem = research_problem(row)
    models = split_values(row.get("model_family", ""))
    optimizations = split_values(row.get("optimization_method", ""))
    hardware = split_values(row.get("hardware_platform", ""))
    pieces = [problem]
    if models:
        pieces.append(f"model={ordered_join(models)}")
    if optimizations:
        pieces.append(f"optimization={ordered_join(optimizations)}")
    if hardware:
        pieces.append(f"hardware={ordered_join(hardware)}")
    return " | ".join(pieces)


def limitations(row: dict[str, str]) -> str:
    missing = []
    if not split_values(row.get("hardware_platform", "")):
        missing.append("missing_hardware_platform")
    if not split_values(row.get("model_family", "")):
        missing.append("missing_model_architecture")
    if not split_values(row.get("optimization_method", "")):
        missing.append("missing_optimization_method")
    metrics = split_values(row.get("metrics_evidence", ""))
    if not (metrics & HARD_DEPLOYMENT_METRICS):
        missing.append("missing_hard_deployment_metrics")
    if not (metrics & {"power", "energy"}):
        missing.append("missing_power_or_energy")
    if not (metrics & {"memory", "RAM", "flash"}):
        missing.append("missing_memory")
    if find_dataset(" ".join([row.get("title", ""), row.get("abstract", "")])) == "not_reported":
        missing.append("missing_dataset")
    if not missing:
        missing.append("none_from_abstract")
    missing.append("abstract_only_evidence")
    return "; ".join(missing)


def gap_relevance(row: dict[str, str]) -> str:
    flags = set(split_values(row.get("gap_flags", "")))
    hardware = split_values(row.get("hardware_platform", ""))
    metrics = split_values(row.get("metrics_evidence", ""))
    models = split_values(row.get("model_family", ""))
    optimizations = split_values(row.get("optimization_method", ""))
    tasks = split_values(row.get("uav_task", ""))

    gaps = set()
    if hardware & MCU_HARDWARE:
        gaps.add("microcontroller_tinyml_gap")
    if hardware & EDGE_GPU_HARDWARE and not (hardware & MCU_HARDWARE):
        gaps.add("microcontroller_tinyml_gap")
    if not (metrics & HARD_DEPLOYMENT_METRICS):
        gaps.add("deployment_metrics_gap")
    if models and not optimizations:
        gaps.add("optimization_gap")
    if any(model.startswith("YOLO") for model in models):
        gaps.add("model_diversity_gap")
    if "object detection" in tasks:
        gaps.add("task_diversity_gap")
    if row.get("benchmark_ready_score", "0") not in {"5"}:
        gaps.add("benchmark_standardization_gap")

    if "missing_hardware_platform" in flags or "missing_metrics" in flags:
        gaps.add("benchmark_standardization_gap")
    return "; ".join(sorted(gaps)) if gaps else "general_supporting_evidence"


def evidence_confidence(row: dict[str, str]) -> str:
    score = 0
    if split_values(row.get("model_family", "")):
        score += 1
    if split_values(row.get("hardware_platform", "")):
        score += 1
    if split_values(row.get("uav_task", "")):
        score += 1
    if split_values(row.get("metrics_evidence", "")):
        score += 1
    if split_values(row.get("optimization_method", "")):
        score += 1
    if score >= 4:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def extract_row(row: dict[str, str], index: int) -> dict[str, str]:
    text = " ".join([row.get("title", ""), row.get("abstract", "")])
    metrics = split_values(row.get("metrics_evidence", ""))
    return {
        "paper_id": f"C{index:03d}",
        "core_rank": row.get("core_rank", ""),
        "core_score": row.get("core_score", ""),
        "title": row.get("title", ""),
        "year": row.get("year", ""),
        "venue": row.get("venue", ""),
        "quartile": row.get("quartile", ""),
        "link": link_for(row),
        "research_problem": research_problem(row),
        "uav_task": row.get("uav_task", "") or "not_reported",
        "model": row.get("model_family", "") or "not_reported",
        "optimization": row.get("optimization_method", "") or "not_reported",
        "hardware": row.get("hardware_platform", "") or "not_reported",
        "deployment_setting": deployment_setting(row, text),
        "dataset": find_dataset(text),
        "accuracy_metrics": ordered_join(metrics & ACCURACY_METRICS),
        "deployment_metrics": ordered_join(metrics & DEPLOYMENT_METRICS),
        "reported_tradeoff": tradeoff(row, text),
        "main_contribution": contribution(row),
        "limitations_or_missing_info": limitations(row),
        "gap_relevance": gap_relevance(row),
        "evidence_confidence": evidence_confidence(row),
        "abstract": row.get("abstract", ""),
        "doi": row.get("doi", ""),
        "pdf_url": row.get("pdf_url", ""),
        "openalex_id": row.get("openalex_id", ""),
    }


def benchmark_ready(row: dict[str, str]) -> bool:
    return all(
        row[field] != "not_reported"
        for field in ["uav_task", "model", "hardware", "accuracy_metrics", "deployment_metrics"]
    ) and bool(split_values(row["deployment_metrics"]) & HARD_DEPLOYMENT_METRICS)


def build_gap_matrix(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    counter = Counter()
    examples: dict[str, list[str]] = {}
    for row in rows:
        for gap in split_values(row.get("gap_relevance", "")):
            counter[gap] += 1
            examples.setdefault(gap, [])
            if len(examples[gap]) < 5:
                examples[gap].append(row["title"])
    return [
        {
            "gap_theme": gap,
            "paper_count": str(count),
            "example_papers": " || ".join(examples.get(gap, [])),
        }
        for gap, count in counter.most_common()
    ]


def build_summary(rows: list[dict[str, str]], benchmark_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    summary: list[dict[str, str]] = []

    def add(section: str, name: str, count: int) -> None:
        summary.append({"section": section, "name": name, "count": str(count)})

    add("total", "core_papers", len(rows))
    add("total", "benchmark_ready_core", len(benchmark_rows))
    for field in ["deployment_setting", "evidence_confidence", "reported_tradeoff"]:
        for name, count in Counter(row[field] for row in rows).most_common():
            add(field, name, count)
    for field in ["model", "optimization", "hardware", "uav_task", "accuracy_metrics", "deployment_metrics"]:
        counter = Counter()
        for row in rows:
            for item in split_values(row[field]):
                counter[item] += 1
        for name, count in counter.most_common():
            add(field, name, count)
    return summary


def main() -> None:
    args = parse_args()
    _, rows = read_csv(args.input)
    rows.sort(key=lambda row: int(row.get("core_rank", "999") or 999))

    evidence_rows = [extract_row(row, index) for index, row in enumerate(rows, start=1)]
    benchmark_rows = [row for row in evidence_rows if benchmark_ready(row)]
    gap_rows = build_gap_matrix(evidence_rows)
    summary_rows = build_summary(evidence_rows, benchmark_rows)

    write_csv(args.output_dir / "evidence_table.csv", evidence_rows, EVIDENCE_COLUMNS)
    write_csv(args.output_dir / "benchmark_ready_core.csv", benchmark_rows, EVIDENCE_COLUMNS)
    write_csv(args.output_dir / "gap_support_matrix.csv", gap_rows, ["gap_theme", "paper_count", "example_papers"])
    write_csv(args.output_dir / "evidence_summary.csv", summary_rows, ["section", "name", "count"])

    print(f"Core papers: {len(evidence_rows)}")
    print(f"Benchmark-ready core papers: {len(benchmark_rows)}")
    print(f"Gap themes: {len(gap_rows)}")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
