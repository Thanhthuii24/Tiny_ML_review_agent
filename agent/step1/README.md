# STEP 1 - Literature Collection Pipeline

Muc tieu: tao raw paper database cho de tai:

```text
Lightweight Deep Learning and TinyML for UAV Edge Deployment
```

Output:

- `data/raw/raw_papers.csv`
- `data/raw/raw_papers.xlsx`

Pipeline nay dung OpenAlex API lam nguon metadata chinh. Script chi dung Python standard library, khong bat buoc cai `requests` hay `pandas`.

## Chay nhanh

```powershell
python agent\step1\scripts\collect.py --email your_email@example.com
```

Lay nhieu hon:

```powershell
python agent\step1\scripts\collect.py --per-page 50 --max-pages 2 --email your_email@example.com
```

Lay rong hon de tao candidate pool khoang 500-2000 papers:

```powershell
python agent\step1\scripts\collect.py --expanded-queries --query-limit 80 --per-page 25 --max-pages 1 --timeout 10 --max-retries 1 --email your_email@example.com
```

Neu mang on dinh hon, co the tang:

```powershell
python agent\step1\scripts\collect.py --expanded-queries --query-limit 120 --per-page 50 --max-pages 1 --timeout 12 --max-retries 1 --email your_email@example.com
```

Uoc luong:

- `80 queries x 25 results` = toi da 2000 raw records truoc dedup/filter.
- `120 queries x 50 results` = toi da 6000 raw records truoc dedup/filter, phu hop neu can pool rat rong.

Chay voi query rieng:

```powershell
python agent\step1\scripts\collect.py --query "TinyML UAV" --query "MobileNet drone detection"
```

## Output trung gian

- `data/raw/openalex_raw.csv`: toan bo ket qua API truoc dedup/filter.
- `data/raw/raw_papers.csv`: ket qua sau dedup va rule filtering.
- `data/raw/raw_papers.xlsx`: ban Excel cua file tren.

## Cot cuoi cung

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

Step 1 khong nham tim paper hoan hao ngay. Muc tieu la tao candidate pool rong nhung co lien quan, sau do Step 2 se loc bang LLM.
