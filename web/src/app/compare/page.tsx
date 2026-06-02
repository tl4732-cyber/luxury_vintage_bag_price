"use client";

import { useState } from "react";
import { searchProducts, getMarketplaceCompare, type ProductSearchResult } from "@/lib/api";

export default function ComparePage() {
  const [selected, setSelected] = useState<ProductSearchResult[]>([]);
  const [query, setQuery] = useState("");
  const [comparisons, setComparisons] = useState<
    { product: ProductSearchResult; spread: string | null; medians: Record<string, number> | null }[]
  >([]);

  async function addProduct() {
    const results = await searchProducts(query);
    if (results[0] && !selected.find((s) => s.id === results[0].id)) {
      const next = [...selected, results[0]].slice(0, 3);
      setSelected(next);
      const comps = await Promise.all(
        next.map(async (p) => {
          try {
            const c = await getMarketplaceCompare(p.id);
            return {
              product: p,
              spread: c.spread_amount,
              medians: c.medians_by_marketplace,
            };
          } catch {
            return { product: p, spread: null, medians: null };
          }
        })
      );
      setComparisons(comps);
    }
  }

  return (
    <div>
      <h1>Compare products</h1>
      <p style={{ color: "var(--muted)" }}>
        Add up to 3 products to compare marketplace medians and spread.
      </p>
      <div className="search-form">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search to add product"
        />
        <button type="button" onClick={addProduct}>
          Add
        </button>
      </div>

      {comparisons.map(({ product, spread, medians }) => (
        <div key={product.id} className="card">
          <h3>
            {product.brand_name} {product.model_name}
          </h3>
          <p>Median: {product.median_price ? `$${Number(product.median_price).toLocaleString()}` : "—"}</p>
          {spread && <p>Marketplace spread: ${Number(spread).toLocaleString()}</p>}
          {medians && (
            <ul>
              {Object.entries(medians).map(([mp, price]) => (
                <li key={mp}>
                  {mp}: ${Number(price).toLocaleString()}
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}
