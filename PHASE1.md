# Phase 1 — Scrapy (step by step)

Build the scraper first. Ignore database, API, and dashboard until later phases.

## Roadmap

| Step | What you build | How to verify |
|------|----------------|---------------|
| **1** ✅ | Scrapy project skeleton, `ListingItem`, settings, pass-through pipeline | `scrapy list` |
| **2** ✅ | `dev_sample` spider — 2 mock bag listings to JSON | `scrapy crawl dev_sample -o out.json` |
| **3** ✅ | eBay Browse API spider (real data when `.env` has keys) | `scrapy crawl ebay_api -o out.json` |
| **4** ✅ | Validation + normalization pipelines | Bad items dropped in logs |
| **5** ✅ | The RealReal spider (Playwright) | `scrapy crawl therealreal -o out.json` |
| **6** ✅ | Postgres pipelines (local Docker) | Rows in `listings` + `price_observations` |

Reference project: `../Scrapy_practice` (same layout and style).

## Step 1 — Done in this branch

```
scrapers/
├── scrapy.cfg
└── bags/
    ├── items.py       # ListingItem fields
    ├── settings.py    # throttling, pipelines
    ├── pipelines.py   # Validation → Normalization → pass-through
    ├── schemas.py     # Pydantic rules
    ├── utils.py       # condition + hash helpers
    ├── middlewares.py
    └── spiders/
        ├── dev_sample.py
        ├── ebay_api.py
        └── therealreal.py
```

```bash
cd scrapers
source ../.venv/bin/activate   # or: python3 -m venv ../.venv && pip install scrapy itemadapter
pip install -r ../requirements-scrapers.txt
scrapy list
```

## Step 2 — Done

`dev_sample` yields two mock listings (eBay Chanel + TRR Hermès). No network required.

```bash
cd scrapers
scrapy crawl dev_sample -o out.json
cat out.json
```

Optional unit test:

```bash
cd scrapers
PYTHONPATH=. pytest tests/test_dev_sample_spider.py -v
```

## Step 3 — Done

`ebay_api` calls the eBay Browse API when credentials exist; otherwise it logs a warning and yields 2 mock eBay items.

**Setup credentials**

```bash
cp .env.example .env
# Edit .env — EBAY_CLIENT_ID (App ID), EBAY_CLIENT_SECRET (Cert ID), EBAY_ENV=sandbox
```

**Run**

```bash
cd scrapers
scrapy crawl ebay_api -o out.json
# One search query, fewer results:
scrapy crawl ebay_api -a query="Louis Vuitton speedy" -a limit=10 -o out.json
```

**Test**

```bash
cd scrapers
PYTHONPATH=. pytest tests/test_ebay_api_spider.py -v
```

## Step 4 — Done

Two pipelines run on every item before export:

1. **ValidationPipeline** — requires `marketplace`, `url`, `source_listing_id`, `price_amount > 0`; drops bad rows
2. **NormalizationPipeline** — trims title, uppercases currency, maps `condition_raw` → `condition_normalized`, adds `scraped_at` + `content_hash`

```bash
cd scrapers
scrapy crawl dev_sample -o out.json
cat out.json   # see condition_normalized, content_hash, scraped_at
```

**Test pipelines**

```bash
cd scrapers
PYTHONPATH=. pytest tests/test_pipelines.py tests/test_utils.py -v
```

**See a drop in logs** (invalid price):

```python
# In a Python shell — price 0 triggers DropItem
from bags.pipelines import ValidationPipeline
from scrapy.exceptions import DropItem
```

Or run `dev_sample` — all sample items pass validation.

## Step 5 — Done

`therealreal` scrapes Chanel/Hermès handbag category pages with **scrapy-playwright**.

**Mock mode (no browser, good for first test)**

```bash
cd scrapers
scrapy crawl therealreal -a use_mock=1 -o out.json
cat out.json
```

**Live scrape**

```bash
pip install -r ../requirements-scrapers.txt
playwright install chromium
scrapy crawl therealreal -o out.json
```

**Test**

```bash
cd scrapers
PYTHONPATH=. pytest tests/test_therealreal_spider.py -v
```

**Why live scrape often returns `[]`:** TRR uses PerimeterX bot protection (HTTP 403 + captcha). This is expected for headless scrapers — not a pip/playwright install problem.

**Workaround for Phase 1:** use `use_mock=1` for TRR shape testing; use `ebay_api` for real prices.

## Step 6 — Done

Listings and price history are stored in **local Postgres** (Docker).

**One-time setup**

```bash
# from project root
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-scrapers.txt
bash scripts/setup_db.sh
```

Add to `.env` (or use defaults):

```env
DATABASE_URL=postgresql://lvbp:lvbp_dev@localhost:5432/luxury_bags
```

**Scrape into the database**

```bash
cd scrapers
scrapy crawl dev_sample          # 2 mock rows
scrapy crawl ebay_api -a query="Chanel bag" -a limit=5   # real eBay
```

**Verify**

```bash
bash scripts/query_db.sh
```

**Tables**

- `marketplaces` — ebay, therealreal
- `listings` — one row per marketplace listing (upserted each crawl)
- `price_observations` — append-only; new row only when price changes

**Phase 1 complete.** Next phases (outside this doc): SQL analytics views, FastAPI, dashboard.
