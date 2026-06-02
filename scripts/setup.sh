#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Starting Postgres and Redis..."
docker compose up -d

echo "Installing Python dependencies..."
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium 2>/dev/null || true

echo "Running migrations..."
export DATABASE_URL="${DATABASE_URL:-postgresql://lvbp:lvbp_dev@localhost:5432/luxury_bags}"
alembic -c db/alembic.ini upgrade head

echo "Seeding catalog..."
python db/seed.py

echo "Applying analytics views..."
python analytics/apply_views.py

echo "Setup complete."
