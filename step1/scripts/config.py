"""Configuration for STEP 1 literature collection."""

LIGHTWEIGHT_MODELS = [
    "MobileNet",
    "EfficientNet",
    "ShuffleNet",
    "TinyViT",
    "MCUNet",
    "GhostNet",
]

MODEL_OPTIMIZATION = [
    "quantization",
    "pruning",
    "knowledge distillation",
    "neural architecture search",
    "low-bit inference",
]

EDGE_DEPLOYMENT = [
    "Jetson Nano",
    "Raspberry Pi",
    "ESP32",
    "STM32",
    "TinyML",
    "embedded AI",
    "edge inference",
]

UAV_TASKS = [
    "UAV object detection",
    "drone surveillance",
    "aerial monitoring",
    "aerial tracking",
    "agriculture drone",
]

BASE_QUERIES = [
    "TinyML UAV",
    "MobileNet drone detection",
    "quantized CNN UAV",
    "Jetson Nano object detection",
    "MCUNet aerial monitoring",
    "embedded AI drone",
    "lightweight deep learning UAV",
    "edge inference drone",
    "EfficientNet UAV object detection",
    "pruning quantization drone detection",
]

REJECT_WORDS = [
    "routing",
    "swarm",
    "communication protocol",
    "path planning",
]

FINAL_COLUMNS = [
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
