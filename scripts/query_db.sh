#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

docker compose exec -T postgres psql -U lvbp -d luxury_bags -c "
SELECT l.id, m.code AS marketplace,
       b.name AS brand, mo.name AS model,
       pv.size, pv.color, pv.leather,
       l.title, po.price_amount, po.currency, po.observed_at
FROM listings l
JOIN marketplaces m ON m.id = l.marketplace_id
LEFT JOIN product_variants pv ON pv.id = l.product_variant_id
LEFT JOIN models mo ON mo.id = pv.model_id
LEFT JOIN brands b ON b.id = mo.brand_id
LEFT JOIN LATERAL (
  SELECT price_amount, currency, observed_at
  FROM price_observations
  WHERE listing_id = l.id
  ORDER BY observed_at DESC
  LIMIT 1
) po ON true
ORDER BY l.id;
"
