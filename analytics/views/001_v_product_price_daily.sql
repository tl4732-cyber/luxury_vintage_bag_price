-- Daily median ask price per product and marketplace
CREATE OR REPLACE VIEW v_product_price_daily AS
SELECT
    l.product_id,
    m.code AS marketplace,
    date_trunc('day', po.observed_at AT TIME ZONE 'UTC')::date AS price_date,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY po.price_amount) AS median_price,
    percentile_cont(0.25) WITHIN GROUP (ORDER BY po.price_amount) AS p25_price,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY po.price_amount) AS p75_price,
    avg(po.price_amount) AS mean_price,
    count(*) AS observation_count,
    count(DISTINCT l.id) AS listing_count
FROM price_observations po
JOIN listings l ON l.id = po.listing_id
JOIN marketplaces m ON m.id = l.marketplace_id
WHERE l.status = 'active'
  AND po.price_type = 'ask'
  AND l.product_id IS NOT NULL
GROUP BY l.product_id, m.code, date_trunc('day', po.observed_at AT TIME ZONE 'UTC')::date;
