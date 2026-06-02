"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  getProduct,
  getProductMetrics,
  getProductPrices,
  getMarketplaceCompare,
  type PricePoint,
  type ProductMetrics,
  type MarketplaceCompare,
} from "@/lib/api";

export default function ProductDetailPage({
  params,
}: {
  params: { productId: string };
}) {
  const id = Number(params.productId);
  const [product, setProduct] = useState<Record<string, unknown> | null>(null);
  const [metrics, setMetrics] = useState<ProductMetrics | null>(null);
  const [prices, setPrices] = useState<PricePoint[]>([]);
  const [compare, setCompare] = useState<MarketplaceCompare | null>(null);
  const [range, setRange] = useState("90d");

  useEffect(() => {
    getProduct(id).then(setProduct).catch(() => setProduct(null));
    getProductMetrics(id).then(setMetrics).catch(() => setMetrics(null));
    getMarketplaceCompare(id).then(setCompare).catch(() => setCompare(null));
  }, [id]);

  useEffect(() => {
    getProductPrices(id, range).then(setPrices).catch(() => setPrices([]));
  }, [id, range]);

  const chartData = prices.map((p) => ({
    date: p.price_date,
    median: Number(p.median_price),
    marketplace: p.marketplace || "all",
  }));

  const brand = (product?.brand as { name?: string })?.name;
  const model = (product?.model as { name?: string })?.name;

  return (
    <div>
      <h1>
        {brand} {model}
      </h1>
      {product?.size && <p>Size: {String(product.size)}</p>}

      {metrics && (
        <div className="metrics-grid">
          <div className="metric">
            <div className="value">
              {metrics.median_price
                ? `$${Number(metrics.median_price).toLocaleString()}`
                : "—"}
            </div>
            <div className="label">Median price</div>
          </div>
          <div className="metric">
            <div className="value">{metrics.active_listing_count ?? "—"}</div>
            <div className="label">Active listings</div>
          </div>
          <div className="metric">
            <div className="value">
              {metrics.min_price
                ? `$${Number(metrics.min_price).toLocaleString()}`
                : "—"}
            </div>
            <div className="label">Low</div>
          </div>
          <div className="metric">
            <div className="value">
              {metrics.max_price
                ? `$${Number(metrics.max_price).toLocaleString()}`
                : "—"}
            </div>
            <div className="label">High</div>
          </div>
        </div>
      )}

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Price trend</h2>
          <select value={range} onChange={(e) => setRange(e.target.value)}>
            <option value="7d">7 days</option>
            <option value="30d">30 days</option>
            <option value="90d">90 days</option>
            <option value="365d">1 year</option>
          </select>
        </div>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis tickFormatter={(v) => `$${v}`} />
              <Tooltip formatter={(v: number) => `$${v.toLocaleString()}`} />
              <Legend />
              <Line type="monotone" dataKey="median" stroke="#8b6914" name="Median" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p>No price history yet.</p>
        )}
      </div>

      {compare?.medians_by_marketplace && (
        <div className="card">
          <h2>Marketplace comparison</h2>
          <table>
            <thead>
              <tr>
                <th>Marketplace</th>
                <th>Median (30d)</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(compare.medians_by_marketplace).map(([mp, price]) => (
                <tr key={mp}>
                  <td>{mp}</td>
                  <td>${Number(price).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {compare.spread_amount && (
            <p>
              Spread: <strong>${Number(compare.spread_amount).toLocaleString()}</strong>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
