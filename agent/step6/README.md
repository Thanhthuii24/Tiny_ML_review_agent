# STEP 6 - Evidence Extraction

Muc tieu: trich bang bang chung chi tiet tu 60 core papers de phuc vu
research gap va benchmark table.

Input:

```text
agent/step5/data/processed/core_papers.csv
```

Output:

- `data/processed/evidence_table.csv`
- `data/processed/benchmark_ready_core.csv`
- `data/processed/gap_support_matrix.csv`
- `data/processed/evidence_summary.csv`

## Chay

```powershell
python agent\step6\scripts\extract_evidence.py
```

## Nguyen tac

- Chi trich thong tin co trong title/abstract/taxonomy metadata.
- Neu abstract khong noi ro thi ghi `not_reported`.
- Cac gia tri `inferred_from_abstract` chi la suy luan tu keyword, can check lai
  khi doc full text.

