#!/usr/bin/env bash 
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" 

export DATABASE_URL="${DATABASE_URL:-postgresql://lvbp:lvbp_dev@localhost:5432/luxury_bags}" 

echo "Starting Postgres (Docker)..." 
docker compose up -d 

echo "Waiting for Postgres..."
for i in {1..30}; do
  if docker compose exec -T postgres pg_isready -U lvbp -d luxury_bags >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

source .venv/bin/activate
pip install -q -r requirements-scrapers.txt

echo "Running migrations..."
# Alembic Reads migration files in db/migrations and applies them to the database.
alembic -c db/alembic.ini upgrade head 

echo "Database ready."
echo "DATABASE_URL=$DATABASE_URL"
