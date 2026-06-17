#!/usr/bin/env bash
# Run The RealReal spider from project root.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

source .venv/bin/activate
pip install -q -r requirements-scrapers.txt
playwright install chromium

cd scrapers
MODE="${1:-live}"
if [[ "$MODE" == "mock" ]]; then
  echo "Running TRR spider in mock mode (no browser)..."
  scrapy crawl therealreal -a use_mock=1 -o out.json
else
  echo "Running TRR spider live (may get 403 from bot protection)..."
  scrapy crawl therealreal -o out.json
fi
echo "Output: scrapers/out.json"
python3 -m json.tool out.json 2>/dev/null || cat out.json
