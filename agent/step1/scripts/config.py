"""STEP 1 configuration: scope, keyword groups, queries, and filters."""

RESEARCH_SCOPE = "Lightweight Deep Learning and TinyML for UAV Edge Deployment"

CATEGORIES = [
    "01_lightweight_models",
    "02_model_optimization",
    "03_edge_deployment",
    "04_uav_tasks",
]

LIGHTWEIGHT_MODELS = [
    "MobileNet",
    "EfficientNet",
    "ShuffleNet",
    "TinyViT",
    "MCUNet",
    "GhostNet",
    "SqueezeNet",
    "YOLOv5n",
    "YOLOv8n",
    "YOLO-NAS",
    "NanoDet",
    "PP-YOLO",
    "EfficientDet",
    "YOLO-Tiny",
    "Tiny YOLO",
    "lightweight CNN",
    "compact CNN",
]

MODEL_OPTIMIZATION = [
    "quantization",
    "pruning",
    "knowledge distillation",
    "neural architecture search",
    "NAS",
    "low-bit inference",
    "model compression",
    "binary neural network",
    "integer inference",
    "8-bit inference",
    "hardware-aware NAS",
    "network slimming",
]

EDGE_DEPLOYMENT = [
    "Jetson Nano",
    "Jetson Xavier NX",
    "Jetson TX2",
    "Raspberry Pi",
    "Google Coral",
    "Edge TPU",
    "ESP32",
    "STM32",
    "microcontroller",
    "MCU",
    "TinyML",
    "embedded AI",
    "edge inference",
    "edge AI",
    "real-time inference",
    "low-power AI",
]

UAV_TASKS = [
    "UAV object detection",
    "drone object detection",
    "aerial object detection",
    "drone surveillance",
    "aerial monitoring",
    "aerial tracking",
    "agriculture drone",
    "UAV remote sensing",
    "drone imagery",
    "UAV imagery",
    "aerial image analysis",
    "UAV vision",
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
    "TinyML drone object detection",
    "low-bit inference UAV",
    "knowledge distillation drone detection",
    "Raspberry Pi UAV object detection",
    "STM32 TinyML vision",
    "ESP32 TinyML object detection",
    "lightweight CNN UAV object detection",
    "compact neural network drone detection",
    "Tiny YOLO UAV detection",
    "YOLO-Tiny drone detection",
    "YOLOv5n UAV object detection",
    "YOLOv8n drone object detection",
    "EfficientDet UAV",
    "SqueezeNet drone",
    "NanoDet UAV",
    "model compression UAV object detection",
    "8-bit inference drone detection",
    "integer inference UAV",
    "binary neural network UAV",
    "hardware-aware NAS edge drone",
    "real-time UAV object detection edge",
    "low-power AI drone vision",
    "Edge TPU drone detection",
    "Google Coral UAV object detection",
    "Jetson Xavier NX UAV detection",
    "Jetson TX2 drone detection",
    "microcontroller TinyML drone",
    "MCU UAV vision",
    "embedded vision UAV",
    "edge AI UAV surveillance",
    "aerial object detection lightweight",
    "UAV remote sensing lightweight deep learning",
    "drone imagery efficient CNN",
    "agriculture UAV lightweight CNN",
]


def generate_expanded_queries(limit: int | None = None) -> list[str]:
    """Generate broader OpenAlex search queries from the keyword groups."""
    queries = list(BASE_QUERIES)

    for model in LIGHTWEIGHT_MODELS:
        for task in [
            "UAV object detection",
            "drone detection",
            "aerial monitoring",
            "UAV imagery",
        ]:
            queries.append(f"{model} {task}")

    for optimization in MODEL_OPTIMIZATION:
        for task in [
            "UAV",
            "drone object detection",
            "aerial image analysis",
            "edge inference",
        ]:
            queries.append(f"{optimization} {task}")

    for device in EDGE_DEPLOYMENT:
        for task in [
            "object detection",
            "UAV",
            "drone",
            "embedded vision",
        ]:
            queries.append(f"{device} {task}")

    for task in UAV_TASKS:
        for qualifier in [
            "lightweight deep learning",
            "TinyML",
            "edge AI",
            "real-time inference",
        ]:
            queries.append(f"{qualifier} {task}")

    deduped_queries = list(dict.fromkeys(queries))
    if limit is not None:
        return deduped_queries[:limit]
    return deduped_queries

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
