"use client";

import { useState } from "react";
import { searchProducts, type ProductSearchResult } from "@/lib/api";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [brand, setBrand] = useState("");
  const [results, setResults] = useState<ProductSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await searchProducts(query, brand || undefined);
      setResults(data);
    } catch {
      setError("Could not reach API. Start the backend with: uvicorn api.main:app --reload");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1>Luxury Vintage Handbag Prices</h1>
      <p className="subtitle" style={{ color: "var(--muted)" }}>
        Search, track trends, and compare prices across eBay and The RealReal.
      </p>

      <form className="search-form" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Brand or model (e.g. Chanel Classic Flap)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select value={brand} onChange={(e) => setBrand(e.target.value)}>
          <option value="">All brands</option>
          <option value="chanel">Chanel</option>
          <option value="hermes">Hermès</option>
          <option value="louis-vuitton">Louis Vuitton</option>
          <option value="gucci">Gucci</option>
          <option value="prada">Prada</option>
        </select>
        <button type="submit" disabled={loading}>
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      <div className="card">
        <h2>Results</h2>
        {results.length === 0 && !loading && <p>No results yet. Run scrapers and seed data first.</p>}
        <table>
          <thead>
            <tr>
              <th>Brand</th>
              <th>Model</th>
              <th>Median price</th>
              <th>Listings</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={r.id}>
                <td>{r.brand_name}</td>
                <td>
                  <a className="product-link" href={`/bags/${r.id}`}>
                    {r.model_name}
                  </a>
                </td>
                <td>
                  {r.median_price
                    ? `$${Number(r.median_price).toLocaleString()}`
                    : "—"}
                </td>
                <td>{r.active_listing_count ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
