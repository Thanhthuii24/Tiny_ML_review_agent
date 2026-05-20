"""Classify final KEEP papers into review taxonomy categories."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


STEP4_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = STEP4_DIR.parents[1]
DEFAULT_INPUT = PROJECT_DIR / "agent" / "step3" / "data" / "processed" / "final_keep_papers.csv"
DEFAULT_OUTPUT_DIR = STEP4_DIR / "data" / "processed"


CATEGORY_PATTERNS = {
    "tinyml_edge_deployment": [
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
        r"arduino",
        r"low-power",
        r"low power",
    ],
    "lightweight_models": [
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
        r"yolo-nano",
        r"slim",
    ],
    "model_optimization": [
        r"quantization",
        r"quantized",
        r"\bint8\b",
        r"pruning",
        r"pruned",
        r"knowledge distillation",
        r"distillation",
        r"compression",
        r"compressed",
        r"low-bit",
        r"low bit",
        r"neural architecture search",
        r"\bnas\b",
        r"approximate computing",
    ],
    "uav_vision_tasks": [
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
        r"disaster",
        r"search and rescue",
        r"landing",
        r"navigation",
        r"battery",
        r"remaining useful life",
        r"structural health",
    ],
    "surveys_reviews_benchmarks": [
        r"\bsurvey\b",
        r"\breview\b",
        r"systematic literature",
        r"state of the art",
        r"state-of-the-art",
        r"taxonomy",
        r"benchmark",
        r"comparison",
        r"comparative",
    ],
    "hardware_metrics_evidence": [
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
        r"accuracy",
        r"\bmap\b",
        r"precision",
        r"recall",
        r"f1",
    ],
}


EXTRACTION_PATTERNS = {
    "model_family": [
        ("MobileNet", r"\bmobilenet\b"),
        ("EfficientNet", r"\befficientnet\b"),
        ("GhostNet", r"\bghostnet\b"),
        ("ShuffleNet", r"\bshufflenet\b"),
        ("SqueezeNet", r"\bsqueezenet\b"),
        ("TinyViT", r"\btinyvit\b"),
        ("MCUNet", r"\bmcunet\b"),
        ("NanoDet", r"\bnanodet\b"),
        ("YOLOv3", r"\byolov3\b"),
        ("YOLOv4", r"\byolov4\b"),
        ("YOLOv5", r"\byolov5\b"),
        ("YOLOv7", r"\byolov7\b"),
        ("YOLOv8", r"\byolov8\b"),
        ("YOLOX", r"\byolox\b"),
        ("YOLO", r"\byolo\b"),
        ("Vision Transformer", r"\bvision transformer\b"),
        ("CNN", r"\bcnn\b|\bconvolutional neural network\b"),
        ("GAN", r"\bgan\b|generative adversarial"),
    ],
    "optimization_method": [
        ("quantization", r"\bquantization\b"),
        ("quantized", r"\bquantized\b"),
        ("int8", r"\bint8\b"),
        ("pruning", r"\bpruning\b|\bpruned\b"),
        ("knowledge distillation", r"\bknowledge distillation\b"),
        ("distillation", r"\bdistillation\b"),
        ("compression", r"\bcompression\b|\bcompressed\b"),
        ("NAS", r"\bnas\b"),
        ("neural architecture search", r"\bneural architecture search\b"),
        ("low-bit", r"\blow-bit\b|\blow bit\b"),
    ],
    "hardware_platform": [
        ("Jetson Nano", r"\bjetson nano\b"),
        ("Jetson Xavier", r"\bjetson xavier\b"),
        ("Jetson", r"\bjetson\b"),
        ("Raspberry Pi", r"\braspberry pi\b"),
        ("ESP32", r"\besp32\b"),
        ("STM32", r"\bstm32\b"),
        ("Arduino", r"\barduino\b"),
        ("MCU", r"\bmcu\b"),
        ("microcontroller", r"\bmicrocontroller\b"),
        ("FPGA", r"\bfpga\b"),
        ("GPU", r"\bgpu\b"),
        ("CPU", r"\bcpu\b"),
        ("embedded", r"\bembedded\b"),
        ("edge", r"\bedge\b"),
        ("TinyML", r"\btinyml\b"),
    ],
    "uav_task": [
        ("object detection", r"\bobject detection\b"),
        ("target detection", r"\btarget detection\b"),
        ("human detection", r"\bhuman detection\b"),
        ("tracking", r"\btracking\b"),
        ("segmentation", r"\bsegmentation\b"),
        ("classification", r"\bclassification\b"),
        ("inspection", r"\binspection\b"),
        ("monitoring", r"\bmonitoring\b"),
        ("surveillance", r"\bsurveillance\b"),
        ("agriculture", r"\bagriculture\b"),
        ("smart farming", r"\bsmart farming\b"),
        ("crop", r"\bcrop\b"),
        ("wildfire", r"\bwildfire\b"),
        ("fire detection", r"\bfire detection\b"),
        ("search and rescue", r"\bsearch and rescue\b"),
        ("landing", r"\blanding\b"),
        ("navigation", r"\bnavigation\b"),
        ("battery", r"\bbattery\b"),
        ("remaining useful life", r"\bremaining useful life\b"),
        ("structural health", r"\bstructural health\b"),
    ],
    "metrics_evidence": [
        ("accuracy", r"\baccuracy\b"),
        ("mAP", r"\bmap\b"),
        ("precision", r"\bprecision\b"),
        ("recall", r"\brecall\b"),
        ("F1", r"\bf1\b"),
        ("FPS", r"\bfps\b|frames per second"),
        ("latency", r"\blatency\b"),
        ("inference latency", r"\binference latency\b"),
        ("memory", r"\bmemory\b"),
        ("RAM", r"\bram\b"),
        ("flash", r"\bflash\b"),
        ("power", r"\bpower\b"),
        ("energy", r"\benergy\b"),
        ("real-time", r"\breal-time\b"),
        ("realtime", r"\brealtime\b"),
    ],
}


PRIMARY_PRIORITY = [
    "tinyml_edge_deployment",
    "model_optimization",
    "lightweight_models",
    "uav_vision_tasks",
    "surveys_reviews_benchmarks",
    "hardware_metrics_evidence",
]


BASE_COLUMNS = [
    "primary_category",
    "secondary_categories",
    "model_family",
    "optimization_method",
    "hardware_platform",
    "uav_task",
    "metrics_evidence",
    "taxonomy_reason",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build STEP 4 taxonomy outputs.")
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


def has_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def extract_values(text: str, values: list[tuple[str, str]]) -> list[str]:
    found = []
    for value, pattern in values:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(value)
    return sorted(set(found), key=str.lower)


def category_matches(text: str) -> list[str]:
    matches = [
        category
        for category, patterns in CATEGORY_PATTERNS.items()
        if has_pattern(text, patterns)
    ]
    return [category for category in PRIMARY_PRIORITY if category in matches]


def classify(row: dict[str, str]) -> dict[str, str]:
    text = " ".join([row.get("title", ""), row.get("abstract", ""), row.get("evidence_axes", "")])
    categories = category_matches(text)
    primary = categories[0] if categories else "uav_vision_tasks"
    secondary = [category for category in categories if category != primary]

    extracted = {
        field: extract_values(text, values)
        for field, values in EXTRACTION_PATTERNS.items()
    }

    reason_bits = []
    if primary:
        reason_bits.append(f"primary={primary}")
    if secondary:
        reason_bits.append(f"secondary={'; '.join(secondary)}")
    for field, values in extracted.items():
        if values:
            reason_bits.append(f"{field}={'; '.join(values[:6])}")

    return {
        **row,
        "primary_category": primary,
        "secondary_categories": "; ".join(secondary),
        "model_family": "; ".join(extracted["model_family"]),
        "optimization_method": "; ".join(extracted["optimization_method"]),
        "hardware_platform": "; ".join(extracted["hardware_platform"]),
        "uav_task": "; ".join(extracted["uav_task"]),
        "metrics_evidence": "; ".join(extracted["metrics_evidence"]),
        "taxonomy_reason": " | ".join(reason_bits),
    }


def build_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    primary = Counter(row["primary_category"] for row in rows)
    secondary = Counter()
    models = Counter()
    optimizations = Counter()
    hardware = Counter()
    tasks = Counter()
    metrics = Counter()
    years = Counter(row.get("year", "") for row in rows)
    venues = Counter(row.get("venue", "") for row in rows)

    for row in rows:
        for category in row["secondary_categories"].split("; "):
            if category:
                secondary[category] += 1
        for column, counter in [
            ("model_family", models),
            ("optimization_method", optimizations),
            ("hardware_platform", hardware),
            ("uav_task", tasks),
            ("metrics_evidence", metrics),
        ]:
            for item in row[column].split("; "):
                if item:
                    counter[item] += 1

    summary: list[dict[str, str]] = []

    def add(section: str, counter: Counter[str]) -> None:
        for name, count in counter.most_common():
            summary.append({"section": section, "name": name, "count": str(count)})

    add("primary_category", primary)
    add("secondary_category", secondary)
    add("model_family", models)
    add("optimization_method", optimizations)
    add("hardware_platform", hardware)
    add("uav_task", tasks)
    add("metrics_evidence", metrics)
    add("year", years)
    add("venue", venues)
    return summary


def main() -> None:
    args = parse_args()
    input_columns, rows = read_csv(args.input)
    taxonomy_rows = [classify(row) for row in rows]
    output_columns = BASE_COLUMNS + input_columns

    write_csv(args.output_dir / "taxonomy_papers.csv", taxonomy_rows, output_columns)
    write_csv(
        args.output_dir / "taxonomy_summary.csv",
        build_summary(taxonomy_rows),
        ["section", "name", "count"],
    )

    for category in CATEGORY_PATTERNS:
        category_rows = [
            row for row in taxonomy_rows
            if row["primary_category"] == category
            or category in row["secondary_categories"].split("; ")
        ]
        write_csv(args.output_dir / f"{category}.csv", category_rows, output_columns)

    print(f"Input KEEP records: {len(rows)}")
    print(f"Taxonomy records: {len(taxonomy_rows)}")
    print("Primary categories:")
    for category, count in Counter(row["primary_category"] for row in taxonomy_rows).most_common():
        print(f"  {category}: {count}")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
