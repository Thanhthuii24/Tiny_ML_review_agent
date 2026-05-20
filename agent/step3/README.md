# STEP 3 - Abstract Relevance Screening

Muc tieu: loc sau cac paper Q1/Q2 tu STEP 2 thanh:

- `keep`: dung scope review, nen dua vao core candidate set.
- `uncertain`: co lien quan nhung abstract chua du ro, can doc full text/manual check.
- `reject`: lech scope review.

Scope review:

```text
Lightweight Deep Learning and TinyML for UAV Edge Deployment
```

## Tieu chi KEEP

Giu paper neu abstract the hien ro:

- UAV/drone/aerial context; va
- it nhat mot trong cac truc chinh:
  - TinyML/edge/embedded/on-device deployment
  - lightweight model
  - model optimization: quantization, pruning, compression, distillation, NAS
  - deployment evidence: latency, FPS, memory, power, real-time inference

## Chay screening

```powershell
python agent\step3\scripts\screen.py
```

Output:

- `data/processed/screened_papers.csv`: tat ca paper kem decision.
- `data/processed/keep_papers.csv`: paper giu lai.
- `data/processed/uncertain_papers.csv`: paper can check tay.
- `data/processed/reject_papers.csv`: paper bi loai.

## Rescreen UNCERTAIN

Sau lan screen dau, co the xu ly tiep nhom uncertain theo huong
semi-conservative:

```powershell
python agent\step3\scripts\rescreen_uncertain.py
```

Output:

- `data/processed/uncertain_rescreened.csv`
- `data/processed/uncertain_promote_to_keep.csv`
- `data/processed/uncertain_remain_uncertain.csv`
- `data/processed/uncertain_demote_to_reject.csv`
- `data/processed/final_keep_papers.csv`
- `data/processed/final_uncertain_papers.csv`
- `data/processed/final_reject_papers.csv`
