# STEP 5 - Core Paper Selection and Gap Evidence

Muc tieu: chon core papers tu `taxonomy_papers.csv` va tao bang evidence
cho research gap.

Input:

```text
agent/step4/data/processed/taxonomy_papers.csv
```

Output:

- `data/processed/scored_papers.csv`
- `data/processed/core_papers.csv`
- `data/processed/supporting_papers.csv`
- `data/processed/excluded_from_core.csv`
- `data/processed/benchmark_candidate_papers.csv`
- `data/processed/gap_evidence_table.csv`
- `data/processed/core_selection_summary.csv`

## Chay

```powershell
python agent\step5\scripts\select_core.py
```

Mac dinh script chon top 60 core papers, nhung co the thay doi:

```powershell
python agent\step5\scripts\select_core.py --core-limit 50
```

## Score logic

Paper duoc cham diem dua tren:

- UAV/drone/aerial context
- TinyML/edge/embedded deployment
- hardware cu the
- model family cu the
- optimization method
- UAV task
- deployment metrics
- accuracy/mAP/precision/recall metrics
- quartile Q1
- citations
- survey/review/benchmark role

