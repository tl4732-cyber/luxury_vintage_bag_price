#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

docker compose exec -T postgres psql -U lvbp -d luxury_bags -c "
SELECT l.id, m.code AS marketplace, l.title, po.price_amount, po.currency, po.observed_at
FROM listings l
JOIN marketplaces m ON m.id = l.marketplace_id
LEFT JOIN LATERAL (
  SELECT price_amount, currency, observed_at
  FROM price_observations
  WHERE listing_id = l.id
  ORDER BY observed_at DESC
  LIMIT 1
) po ON true
ORDER BY l.id;
"
# show me all scraped listings and their latest prices" 
# for quickly verifying that ETL pipeline is working correctly

# -e: stop on errors
# -u: error on undefined variables
# pipefail: fail if any command in a pipeline fails