-- Price trend % changes on daily medians (7d, 30d, 90d)
CREATE OR REPLACE VIEW v_price_trends AS
WITH daily AS (
    SELECT * FROM v_product_price_daily
),
with_lags AS (
    SELECT
        product_id,
        marketplace,
        price_date,
        median_price,
        lag(median_price, 7) OVER (
            PARTITION BY product_id, marketplace ORDER BY price_date
        ) AS median_7d_ago,
        lag(median_price, 30) OVER (
            PARTITION BY product_id, marketplace ORDER BY price_date
        ) AS median_30d_ago,
        lag(median_price, 90) OVER (
            PARTITION BY product_id, marketplace ORDER BY price_date
        ) AS median_90d_ago
    FROM daily
)
SELECT
    product_id,
    marketplace,
    price_date,
    median_price,
    CASE WHEN median_7d_ago > 0 THEN round(
        ((median_price - median_7d_ago) / median_7d_ago * 100)::numeric, 2
    ) END AS change_7d_pct,
    CASE WHEN median_30d_ago > 0 THEN round(
        ((median_price - median_30d_ago) / median_30d_ago * 100)::numeric, 2
    ) END AS change_30d_pct,
    CASE WHEN median_90d_ago > 0 THEN round(
        ((median_price - median_90d_ago) / median_90d_ago * 100)::numeric, 2
    ) END AS change_90d_pct
FROM with_lags;
