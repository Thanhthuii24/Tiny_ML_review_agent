"""Select core papers and produce research-gap evidence from STEP 4 taxonomy."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


STEP5_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = STEP5_DIR.parents[1]
DEFAULT_INPUT = PROJECT_DIR / "agent" / "step4" / "data" / "processed" / "taxonomy_papers.csv"
DEFAULT_OUTPUT_DIR = STEP5_DIR / "data" / "processed"


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
ACCURACY_METRICS = {"accuracy", "mAP", "precision", "recall", "F1"}
SPECIFIC_HARDWARE = {
    "Jetson Nano",
    "Jetson Xavier",
    "Jetson",
    "Raspberry Pi",
    "ESP32",
    "STM32",
    "Arduino",
    "MCU",
    "microcontroller",
    "FPGA",
}
MCU_HARDWARE = {"ESP32", "STM32", "Arduino", "MCU", "microcontroller"}
EDGE_GPU_HARDWARE = {"Jetson Nano", "Jetson Xavier", "Jetson", "GPU", "FPGA"}


SCORE_COLUMNS = [
    "core_score",
    "core_rank",
    "selection_group",
    "score_reasons",
    "benchmark_ready_score",
    "benchmark_missing_fields",
    "gap_flags",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select STEP 5 core papers.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--core-limit", type=int, default=60)
    parser.add_argument("--supporting-min-score", type=int, default=11)
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


def text_has_uav(row: dict[str, str]) -> bool:
    text = " ".join([row.get("title", ""), row.get("abstract", ""), row.get("evidence_axes", "")])
    return bool(re.search(r"\buav\b|\buavs\b|\bdrone\b|\bdrones\b|unmanned aerial|aerial vehicle", text, re.I))


def citation_points(citations: str) -> tuple[int, str]:
    try:
        value = int(float(citations or 0))
    except ValueError:
        value = 0
    if value >= 100:
        return 3, "citations>=100"
    if value >= 50:
        return 2, "citations>=50"
    if value >= 15:
        return 1, "citations>=15"
    return 0, ""


def score_paper(row: dict[str, str]) -> dict[str, str]:
    score = 0
    reasons: list[str] = []

    categories = {row.get("primary_category", "")} | split_values(row.get("secondary_categories", ""))
    hardware = split_values(row.get("hardware_platform", ""))
    metrics = split_values(row.get("metrics_evidence", ""))
    models = split_values(row.get("model_family", ""))
    optimizations = split_values(row.get("optimization_method", ""))
    tasks = split_values(row.get("uav_task", ""))

    if text_has_uav(row):
        score += 2
        reasons.append("+2 explicit UAV/drone/aerial context")
    if "tinyml_edge_deployment" in categories:
        score += 3
        reasons.append("+3 TinyML/edge/embedded deployment category")
    if hardware & SPECIFIC_HARDWARE:
        score += 3
        reasons.append("+3 specific hardware platform")
    elif hardware:
        score += 1
        reasons.append("+1 generic hardware/platform evidence")
    if models:
        score += 2
        reasons.append("+2 specific model family")
    if optimizations:
        score += 3
        reasons.append("+3 optimization method")
    if tasks:
        score += 2
        reasons.append("+2 UAV task")
    if metrics & DEPLOYMENT_METRICS:
        score += 3
        reasons.append("+3 deployment metrics")
    if metrics & ACCURACY_METRICS:
        score += 1
        reasons.append("+1 accuracy/quality metrics")
    if row.get("quartile", "").upper() == "Q1":
        score += 1
        reasons.append("+1 Q1 venue")
    citation_score, citation_reason = citation_points(row.get("citations", ""))
    if citation_score:
        score += citation_score
        reasons.append(f"+{citation_score} {citation_reason}")
    if "surveys_reviews_benchmarks" in categories:
        score += 2
        reasons.append("+2 survey/review/benchmark role")

    benchmark_fields = {
        "model": bool(models),
        "hardware": bool(hardware),
        "task": bool(tasks),
        "accuracy_metric": bool(metrics & ACCURACY_METRICS),
        "deployment_metric": bool(metrics & DEPLOYMENT_METRICS),
    }
    benchmark_score = sum(1 for present in benchmark_fields.values() if present)
    benchmark_missing = [name for name, present in benchmark_fields.items() if not present]

    gap_flags = []
    if hardware & MCU_HARDWARE:
        gap_flags.append("microcontroller_tinyml_evidence")
    if hardware & EDGE_GPU_HARDWARE:
        gap_flags.append("edge_gpu_dominance_evidence")
    if metrics and not (metrics & DEPLOYMENT_METRICS):
        gap_flags.append("missing_deployment_metrics")
    if models and not optimizations:
        gap_flags.append("model_without_optimization")
    if "YOLO" in models and len(models - {"YOLO"}) == 0:
        gap_flags.append("yolo_dominance_evidence")
    if "object detection" in tasks:
        gap_flags.append("object_detection_dominance_evidence")
    if not hardware:
        gap_flags.append("missing_hardware_platform")
    if not metrics:
        gap_flags.append("missing_metrics")

    return {
        **row,
        "core_score": str(score),
        "score_reasons": " | ".join(reasons),
        "benchmark_ready_score": str(benchmark_score),
        "benchmark_missing_fields": "; ".join(benchmark_missing) if benchmark_missing else "none",
        "gap_flags": "; ".join(gap_flags),
    }


def sort_key(row: dict[str, str]) -> tuple[int, int, int, int]:
    try:
        score = int(row.get("core_score", 0))
    except ValueError:
        score = 0
    try:
        citations = int(float(row.get("citations", 0) or 0))
    except ValueError:
        citations = 0
    benchmark = int(row.get("benchmark_ready_score", 0) or 0)
    q1 = 1 if row.get("quartile", "").upper() == "Q1" else 0
    return score, benchmark, citations, q1


def assign_groups(rows: list[dict[str, str]], core_limit: int, supporting_min_score: int) -> list[dict[str, str]]:
    ranked = sorted(rows, key=sort_key, reverse=True)
    for rank, row in enumerate(ranked, start=1):
        row["core_rank"] = str(rank)
        score = int(row.get("core_score", "0") or 0)
        if rank <= core_limit:
            row["selection_group"] = "core"
        elif score >= supporting_min_score:
            row["selection_group"] = "supporting"
        else:
            row["selection_group"] = "excluded_from_core"
    return ranked


def examples(rows: list[dict[str, str]], predicate, limit: int = 5) -> str:
    selected = [row.get("title", "") for row in rows if predicate(row)]
    return " || ".join(selected[:limit])


def count_rows(rows: list[dict[str, str]], predicate) -> int:
    return sum(1 for row in rows if predicate(row))


def build_gap_table(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    total = len(rows)

    def hardware(row: dict[str, str]) -> set[str]:
        return split_values(row.get("hardware_platform", ""))

    def metrics(row: dict[str, str]) -> set[str]:
        return split_values(row.get("metrics_evidence", ""))

    def models(row: dict[str, str]) -> set[str]:
        return split_values(row.get("model_family", ""))

    def optimizations(row: dict[str, str]) -> set[str]:
        return split_values(row.get("optimization_method", ""))

    def tasks(row: dict[str, str]) -> set[str]:
        return split_values(row.get("uav_task", ""))

    mcu_count = count_rows(rows, lambda row: bool(hardware(row) & MCU_HARDWARE))
    edge_gpu_count = count_rows(rows, lambda row: bool(hardware(row) & EDGE_GPU_HARDWARE))
    deployment_metric_count = count_rows(rows, lambda row: bool(metrics(row) & HARD_DEPLOYMENT_METRICS))
    accuracy_metric_count = count_rows(rows, lambda row: bool(metrics(row) & ACCURACY_METRICS))
    optimization_count = count_rows(rows, lambda row: bool(optimizations(row)))
    yolo_count = count_rows(rows, lambda row: "YOLO" in models(row) or any(item.startswith("YOLO") for item in models(row)))
    object_detection_count = count_rows(rows, lambda row: "object detection" in tasks(row))
    benchmark_ready_count = count_rows(rows, lambda row: int(row.get("benchmark_ready_score", "0") or 0) >= 4)

    return [
        {
            "gap_theme": "microcontroller_tinyml_gap",
            "evidence": f"Only {mcu_count}/{total} core-candidate papers mention MCU-class platforms, while {edge_gpu_count}/{total} mention Jetson/GPU/FPGA-class edge hardware.",
            "paper_count": str(mcu_count),
            "example_papers": examples(rows, lambda row: bool(hardware(row) & MCU_HARDWARE)),
            "why_it_matters": "UAV TinyML claims need validation on ultra-resource-constrained devices, not only edge GPUs.",
            "possible_research_direction": "Energy-aware TinyML deployment for UAV tasks on ESP32/STM32/Cortex-M class devices.",
        },
        {
            "gap_theme": "deployment_metrics_gap",
            "evidence": f"{accuracy_metric_count}/{total} papers mention accuracy-style metrics, but {deployment_metric_count}/{total} mention hard deployment metrics such as FPS, latency, memory, RAM/flash, power, or energy.",
            "paper_count": str(deployment_metric_count),
            "example_papers": examples(rows, lambda row: bool(metrics(row) & HARD_DEPLOYMENT_METRICS)),
            "why_it_matters": "Accuracy alone is insufficient for UAV onboard deployment where latency, memory, and energy constrain flight-time operation.",
            "possible_research_direction": "Report multi-objective trade-offs: accuracy/mAP versus latency, memory footprint, and energy per inference.",
        },
        {
            "gap_theme": "optimization_gap",
            "evidence": f"{optimization_count}/{total} papers mention quantization, pruning, distillation, compression, or NAS.",
            "paper_count": str(optimization_count),
            "example_papers": examples(rows, lambda row: bool(optimizations(row))),
            "why_it_matters": "Many studies adopt lightweight models directly, but fewer systematically optimize them under UAV hardware constraints.",
            "possible_research_direction": "Compare quantization, pruning, distillation, and NAS for the same UAV task and hardware budget.",
        },
        {
            "gap_theme": "model_diversity_gap",
            "evidence": f"YOLO-family models appear in {yolo_count}/{total} papers, indicating strong detector-family concentration.",
            "paper_count": str(yolo_count),
            "example_papers": examples(rows, lambda row: "YOLO" in models(row) or any(item.startswith("YOLO") for item in models(row))),
            "why_it_matters": "YOLO dominance may hide opportunities for TinyML-native architectures and compact transformer/CNN hybrids.",
            "possible_research_direction": "Explore MCUNet/TinyViT/GhostNet/MobileNet-style alternatives under identical UAV deployment constraints.",
        },
        {
            "gap_theme": "task_diversity_gap",
            "evidence": f"Object detection appears in {object_detection_count}/{total} papers, while navigation, battery/RUL, anomaly detection, and onboard decision-making appear far less often.",
            "paper_count": str(object_detection_count),
            "example_papers": examples(rows, lambda row: "object detection" in tasks(row)),
            "why_it_matters": "UAV autonomy depends on more than detection; onboard health, navigation, and anomaly tasks also need efficient AI.",
            "possible_research_direction": "TinyML for UAV battery health, acoustic anomaly detection, navigation support, or multi-modal onboard sensing.",
        },
        {
            "gap_theme": "benchmark_standardization_gap",
            "evidence": f"{benchmark_ready_count}/{total} papers have at least 4 of 5 benchmark fields: model, hardware, task, accuracy metric, and deployment metric. The exported benchmark candidate file further requires a hard deployment metric.",
            "paper_count": str(benchmark_ready_count),
            "example_papers": examples(rows, lambda row: int(row.get("benchmark_ready_score", "0") or 0) >= 4),
            "why_it_matters": "Inconsistent reporting makes fair comparison across UAV edge AI papers difficult.",
            "possible_research_direction": "Create a standardized UAV TinyML benchmark table covering model, hardware, dataset/task, accuracy, latency, memory, and energy.",
        },
    ]


def build_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    summary: list[dict[str, str]] = []
    for section, counter in [
        ("selection_group", Counter(row["selection_group"] for row in rows)),
        ("primary_category", Counter(row["primary_category"] for row in rows)),
        ("quartile", Counter(row["quartile"] for row in rows)),
        ("benchmark_ready_score", Counter(row["benchmark_ready_score"] for row in rows)),
    ]:
        for name, count in counter.most_common():
            summary.append({"section": section, "name": name, "count": str(count)})
    return summary


def main() -> None:
    args = parse_args()
    input_columns, rows = read_csv(args.input)
    scored = [score_paper(row) for row in rows]
    ranked = assign_groups(scored, args.core_limit, args.supporting_min_score)

    output_columns = SCORE_COLUMNS + input_columns
    core = [row for row in ranked if row["selection_group"] == "core"]
    supporting = [row for row in ranked if row["selection_group"] == "supporting"]
    excluded = [row for row in ranked if row["selection_group"] == "excluded_from_core"]
    benchmark = [
        row for row in ranked
        if int(row.get("benchmark_ready_score", "0") or 0) >= 4
        and bool(split_values(row.get("metrics_evidence", "")) & HARD_DEPLOYMENT_METRICS)
    ]

    write_csv(args.output_dir / "scored_papers.csv", ranked, output_columns)
    write_csv(args.output_dir / "core_papers.csv", core, output_columns)
    write_csv(args.output_dir / "supporting_papers.csv", supporting, output_columns)
    write_csv(args.output_dir / "excluded_from_core.csv", excluded, output_columns)
    write_csv(args.output_dir / "benchmark_candidate_papers.csv", benchmark, output_columns)
    write_csv(
        args.output_dir / "gap_evidence_table.csv",
        build_gap_table(ranked),
        ["gap_theme", "evidence", "paper_count", "example_papers", "why_it_matters", "possible_research_direction"],
    )
    write_csv(
        args.output_dir / "core_selection_summary.csv",
        build_summary(ranked),
        ["section", "name", "count"],
    )

    print(f"Input taxonomy records: {len(rows)}")
    print(f"Core papers: {len(core)}")
    print(f"Supporting papers: {len(supporting)}")
    print(f"Excluded from core: {len(excluded)}")
    print(f"Benchmark candidates: {len(benchmark)}")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
