# STEP 4 - Taxonomy Classification

Muc tieu: phan loai cac paper `final_keep_papers.csv` cua STEP 3 thanh
cac nhom noi dung de viet review.

Input:

```text
agent/step3/data/processed/final_keep_papers.csv
```

Output chinh:

- `data/processed/taxonomy_papers.csv`
- `data/processed/taxonomy_summary.csv`
- `data/processed/tinyml_edge_deployment.csv`
- `data/processed/lightweight_models.csv`
- `data/processed/model_optimization.csv`
- `data/processed/uav_vision_tasks.csv`
- `data/processed/surveys_reviews_benchmarks.csv`
- `data/processed/hardware_metrics_evidence.csv`

## Chay

```powershell
python agent\step4\scripts\taxonomy.py
```

## Taxonomy

- `tinyml_edge_deployment`: TinyML, edge, embedded, MCU, Jetson, Raspberry Pi,
  ESP32, STM32, on-device inference.
- `lightweight_models`: MobileNet, YOLO lightweight variants, EfficientNet,
  GhostNet, ShuffleNet, TinyViT, MCUNet, compact CNNs.
- `model_optimization`: quantization, pruning, distillation, NAS, compression,
  low-bit inference.
- `uav_vision_tasks`: object detection, tracking, segmentation, inspection,
  monitoring, agriculture, wildfire, landing/navigation.
- `surveys_reviews_benchmarks`: survey, review, taxonomy, benchmark/comparison.
- `hardware_metrics_evidence`: latency, FPS, memory, RAM/flash, power/energy,
  accuracy, embedded hardware evidence.

