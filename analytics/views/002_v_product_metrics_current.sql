-- Current aggregate metrics per product (active listings, latest medians)
CREATE OR REPLACE VIEW v_product_metrics_current AS
WITH latest_prices AS (
    SELECT DISTINCT ON (po.listing_id)
        po.listing_id,
        l.product_id,
        m.code AS marketplace,
        po.price_amount,
        po.observed_at
    FROM price_observations po
    JOIN listings l ON l.id = po.listing_id
    JOIN marketplaces m ON m.id = l.marketplace_id
    WHERE l.status = 'active'
      AND po.price_type = 'ask'
      AND l.product_id IS NOT NULL
    ORDER BY po.listing_id, po.observed_at DESC
)
SELECT
    product_id,
    count(*) AS active_listing_count,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY price_amount) AS median_price,
    avg(price_amount) AS mean_price,
    min(price_amount) AS min_price,
    max(price_amount) AS max_price,
    percentile_cont(0.25) WITHIN GROUP (ORDER BY price_amount) AS p25_price,
    percentile_cont(0.75) WITHIN GROUP (ORDER BY price_amount) AS p75_price
FROM latest_prices
GROUP BY product_id;
