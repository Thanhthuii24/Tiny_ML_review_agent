# STEP 1 - Literature Collection Pipeline

Muc tieu: tao co so du lieu paper tho cho buoc loc va tom tat ve:

> Lightweight Deep Learning and TinyML for UAV Edge Deployment

Output chinh:

- `data/raw/raw_papers.csv`
- `data/raw/raw_papers.xlsx`

## Cai dat

```powershell
pip install -r step1/requirements.txt
```

## Chay thu thap OpenAlex

Chay mac dinh:

```powershell
python step1/scripts/collect.py
```

Nen them email de OpenAlex nhan dien polite user:

```powershell
python step1/scripts/collect.py --email your_email@example.com
```

Tang so luong ket qua:

```powershell
python step1/scripts/collect.py --per-page 50 --max-pages 2 --email your_email@example.com
```

## Chay tung buoc rieng

Deduplicate lai file raw:

```powershell
python step1/scripts/deduplicate.py --input step1/data/raw/openalex_raw.csv --output step1/data/raw/raw_papers_dedup.csv
```

Loc rule co ban:

```powershell
python step1/scripts/export.py --input step1/data/raw/raw_papers_dedup.csv --csv step1/data/raw/raw_papers.csv --xlsx step1/data/raw/raw_papers.xlsx
```

## Cot du lieu

- `title`
- `abstract`
- `year`
- `authors`
- `venue`
- `citations`
- `doi`
- `query_source`
- `pdf_url`
- `source_api`
- `openalex_id`
- `concepts`

## Ghi chu

Step 1 uu tien recall: lay rong, deduplicate, loai bo paper ro rang lech chu de. Step 2 se dung LLM de loc ky hon.
