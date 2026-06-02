#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/scrapers"
source "$ROOT/.venv/bin/activate"
export DATABASE_URL="${DATABASE_URL:-postgresql://lvbp:lvbp_dev@localhost:5432/luxury_bags}"
export PYTHONPATH="$ROOT/scrapers:$ROOT"

echo "Running eBay API spider..."
scrapy crawl ebay_api

echo "Running The RealReal spider..."
scrapy crawl therealreal

echo "Scrape run complete."
