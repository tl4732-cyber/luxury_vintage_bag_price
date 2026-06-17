# luxury_vintage_bag_price

Track luxury vintage handbag prices. **Phase 1** is Scrapy only — built step by step.

## Start here

Read **[PHASE1.md](PHASE1.md)** for the step-by-step plan.

### Step 1 (current)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-scrapers.txt
cd scrapers
scrapy list
```

### Step 2 — mock data

```bash
cd scrapers
scrapy crawl dev_sample -o out.json
```

### Step 3 — eBay API

```bash
cp .env.example .env   # add EBAY_CLIENT_ID and EBAY_CLIENT_SECRET
cd scrapers
scrapy crawl ebay_api -o out.json
```

Without `.env` credentials, `ebay_api` still writes 2 mock eBay listings so you can test the flow.

### Step 5 — The RealReal (Playwright)

```bash
pip install -r requirements-scrapers.txt
playwright install chromium
cd scrapers
scrapy crawl therealreal -a use_mock=1 -o out.json   # offline test
scrapy crawl therealreal -o out.json                 # live TRR
```

### Step 4 — validation + normalization

Every spider item is validated (bad prices dropped) and enriched with `condition_normalized`, `scraped_at`, and `content_hash`.

```bash
cd scrapers
scrapy crawl dev_sample -o out.json
```

### Step 6 — Postgres (local Docker)

```bash
bash scripts/setup_db.sh
cd scrapers
scrapy crawl dev_sample
bash ../scripts/query_db.sh
```

Phase 1 scraping is complete. API/dashboard are future phases.
