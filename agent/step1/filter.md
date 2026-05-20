# STEP 1 — Literature Collection Pipeline

## Goal

Build a raw literature database from APIs before LLM filtering.

Final outputs:

- raw_papers.csv
- raw_papers.xlsx

This database will later be used by the filtering agent in STEP 2.

---

# STEP 1.1 — Define Research Scope

Define the exact review scope.

Example:

```text
Lightweight Deep Learning and TinyML
for UAV Edge Deployment
```

The scope determines:

- what papers to keep
- what papers to reject
- keyword generation
- filtering logic

---

# STEP 1.2 — Create Research Categories

Create major literature categories.

Example structure:

```text
01_lightweight_models
02_model_optimization
03_edge_deployment
04_uav_tasks
```

These categories become:

- keyword groups
- taxonomy
- future review sections

---

# STEP 1.3 — Create Keyword Groups

## Lightweight Models

```python
LIGHTWEIGHT_MODELS = [
    "MobileNet",
    "EfficientNet",
    "TinyViT",
    "MCUNet",
    "GhostNet",
]
```

## Model Optimization

```python
MODEL_OPTIMIZATION = [
    "quantization",
    "pruning",
    "knowledge distillation",
    "NAS",
]
```

## Edge Deployment

```python
EDGE_DEPLOYMENT = [
    "Jetson Nano",
    "Raspberry Pi",
    "ESP32",
    "STM32",
    "TinyML",
    "embedded AI",
]
```

## UAV Tasks

```python
UAV_TASKS = [
    "UAV object detection",
    "drone surveillance",
    "aerial monitoring",
    "aerial tracking",
]
```

---

# STEP 1.4 — Generate Search Queries

Combine keywords into search queries.

Example:

```python
queries = [
    "TinyML UAV",
    "MobileNet drone detection",
    "quantized CNN UAV",
    "Jetson Nano object detection",
    "MCUNet aerial monitoring",
]
```

Goals:

- maximize recall
- avoid missing important papers
- cover different terminology styles

---

# STEP 1.5 — Call APIs

Recommended APIs:

| API | Purpose |
|---|---|
| OpenAlex | main metadata source |
| Semantic Scholar | related papers |
| arXiv | recent papers |

Example OpenAlex request:

```python
import requests

url = "https://api.openalex.org/works"

params = {
    "search": "TinyML UAV",
    "per-page": 25
}

response = requests.get(url, params=params)

data = response.json()
```

---

# STEP 1.6 — Extract Metadata

Extract the following fields:

- title
- abstract
- year
- authors
- DOI
- venue
- citation count
- concepts
- PDF URL

---

# STEP 1.7 — Reconstruct Abstract

OpenAlex abstracts are stored as inverted indexes.

Convert them into readable text.

Example:

```python
def reconstruct_abstract(inv_idx):

    words = []

    for word, positions in inv_idx.items():
        for pos in positions:
            words.append((pos, word))

    words.sort()

    return " ".join([w for _, w in words])
```

---

# STEP 1.8 — Normalize Paper Format

Convert papers into a unified structure.

Example:

```python
paper = {
    "title": title,
    "abstract": abstract,
    "year": year,
    "doi": doi,
    "citations": cited_by_count,
    "venue": venue,
    "query_source": query,
}
```

---

# STEP 1.9 — Remove Duplicates

Multiple queries may return duplicated papers.

Deduplicate using:

- DOI
- title similarity

Example:

```python
seen = set()

filtered = []

for p in papers:

    if p["doi"] not in seen:
        filtered.append(p)
        seen.add(p["doi"])
```

---

# STEP 1.10 — Basic Rule Filtering

Remove obviously irrelevant papers before LLM filtering.

Reject keywords:

```python
REJECT_WORDS = [
    "routing",
    "swarm",
    "communication protocol",
    "path planning",
]
```

---

# STEP 1.11 — Export CSV / Excel

## CSV Export

```python
import pandas as pd

df = pd.DataFrame(filtered)

df.to_csv("raw_papers.csv", index=False)
```

## Excel Export

```python
df.to_excel("raw_papers.xlsx", index=False)
```

---

# Final CSV Columns

| Column | Purpose |
|---|---|
| title | paper title |
| abstract | LLM filtering |
| year | publication year |
| authors | metadata |
| venue | conference/journal |
| citations | paper impact |
| doi | deduplication |
| query_source | query trace |
| pdf_url | download link |

---

# Expected Results

| Stage | Number of Papers |
|---|---|
| Raw API collection | 500 |
| After deduplication | 300 |
| After rule filtering | 150 |
| After LLM filtering | 40 |
| Final core papers | 20 |

---

# Important Notes

STEP 1 is NOT about:
- finding perfect papers immediately

STEP 1 IS about:
- building a broad but relevant candidate pool

The filtering agent in STEP 2 will refine the collection later.