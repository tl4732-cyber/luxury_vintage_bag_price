-- Marketplace price spread per product (max median - min median across sources)
CREATE OR REPLACE VIEW v_marketplace_spread AS
WITH marketplace_medians AS (
    SELECT
        l.product_id,
        m.code AS marketplace,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY po.price_amount) AS median_price,
        count(DISTINCT l.id) AS listing_count
    FROM price_observations po
    JOIN listings l ON l.id = po.listing_id
    JOIN marketplaces m ON m.id = l.marketplace_id
    WHERE l.status = 'active'
      AND po.price_type = 'ask'
      AND l.product_id IS NOT NULL
      AND po.observed_at >= now() - interval '30 days'
    GROUP BY l.product_id, m.code
)
SELECT
    product_id,
    max(median_price) - min(median_price) AS spread_amount,
    max(median_price) AS highest_marketplace_median,
    min(median_price) AS lowest_marketplace_median,
    jsonb_object_agg(marketplace, median_price) AS medians_by_marketplace,
    sum(listing_count) AS total_listings
FROM marketplace_medians
GROUP BY product_id;
