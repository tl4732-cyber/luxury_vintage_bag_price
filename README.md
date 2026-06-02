# Luxury Vintage Bag Price Platform

Track luxury vintage handbag prices from **eBay** and **The RealReal**, store historical price data in PostgreSQL, and explore trends via a Next.js dashboard.

## Architecture

```
scrapers/ (Scrapy) → PostgreSQL → analytics SQL views → FastAPI → Next.js
```

See the architecture plan in `.cursor/plans/` for full design details.

## Quick start

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 18+ (for dashboard)

### Setup

```bash
cp .env.example .env
make setup
```

### Run scrapers

```bash
make scrapers
# Or individually:
cd scrapers && PYTHONPATH=.:.. scrapy crawl ebay_api
cd scrapers && PYTHONPATH=.:.. scrapy crawl therealreal
```

eBay spider uses **Browse API** when `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET` are set; otherwise it yields mock items for local dev.

### API

```bash
make api
# http://localhost:8000/docs
```

### Dashboard

```bash
cp web/.env.local.example web/.env.local
make web
# http://localhost:3000
```

## Project layout

| Path | Purpose |
|------|---------|
| `scrapers/bags/` | Scrapy spiders, items, pipelines |
| `db/` | SQLAlchemy models, Alembic migrations, seed |
| `analytics/views/` | SQL views for trends and metrics |
| `api/` | FastAPI read endpoints |
| `web/` | Next.js dashboard |
| `sentiment/` | Phase 4 Reddit / Instagram ingest |

## API endpoints

- `GET /api/v1/search?q=chanel`
- `GET /api/v1/products/{id}/metrics`
- `GET /api/v1/products/{id}/prices?range=90d`
- `GET /api/v1/products/{id}/marketplaces`
- `GET /api/v1/facets`

## Tests

```bash
source .venv/bin/activate
PYTHONPATH=scrapers:. pytest scrapers/tests -v
```

## Cron example

```cron
0 */6 * * * /path/to/luxury_vintage_bag_price/scripts/run_scrapers.sh
0 2 * * * cd /path/to/project && .venv/bin/python -m sentiment.ingest_reddit --limit 100
```

## Reference

Scraper structure follows [Scrapy_practice](../Scrapy_practice): explicit items, pipeline lifecycle, conservative throttling, and spider unit tests.
