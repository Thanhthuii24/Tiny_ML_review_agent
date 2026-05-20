# STEP 2 - Abstract, Year, and Quartile Filtering

Muc tieu: loc candidate papers tu STEP 1 cho review:

```text
Lightweight Deep Learning and TinyML for UAV Edge Deployment
```

Dieu kien hien tai:

- Abstract phai co noi dung va lien quan den scope review.
- Nam xuat ban trong khoang `2020-2026`.
- Chi giu venue co quartile `Q1` hoac `Q2`.

## Chay loc

```powershell
python agent\step2\scripts\filter.py
```

Output:

- `data/interim/abstract_year_filtered.csv`: da loc theo abstract + year.
- `data/interim/venue_quartile_template.csv`: danh sach venue can gan quartile.
- `data/interim/needs_quartile_review.csv`: paper da qua abstract/year nhung chua co quartile.
- `data/processed/final_q1_q2_papers.csv`: ket qua final neu da co quartile Q1/Q2.
- `data/processed/rejected_papers.csv`: cac paper bi loai kem ly do.

## Gan quartile

Vi file STEP 1 khong co san cot quartile, hay dien cot `quartile` trong:

```text
agent/step2/data/interim/venue_quartile_template.csv
```

Sau do chay lai:

```powershell
python agent\step2\scripts\filter.py --quartiles agent\step2\data\interim\venue_quartile_template.csv
```

Accepted values: `Q1`, `Q2`, `Q3`, `Q4`. Script chi giu `Q1` va `Q2`.

## Tu dong dien quartile tu file SCImago/SJR

Neu co file CSV tai tu SCImago/SJR, co the merge tu dong:

```powershell
python agent\step2\scripts\import_quartiles.py path\to\scimago_2024.csv
python agent\step2\scripts\filter.py
```

Script se tim cot title/source title/journal title va cot quartile/SJR Quartile,
sau do dien vao `venue_quartile_template.csv` theo ten venue.
