const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type ProductSearchResult = {
  id: number;
  brand_name: string;
  model_name: string;
  size: string | null;
  median_price: string | null;
  active_listing_count: number | null;
};

export type PricePoint = {
  price_date: string;
  marketplace: string | null;
  median_price: string;
  mean_price: string | null;
  listing_count: number | null;
};

export type ProductMetrics = {
  product_id: number;
  active_listing_count: number | null;
  median_price: string | null;
  mean_price: string | null;
  min_price: string | null;
  max_price: string | null;
};

export type MarketplaceCompare = {
  product_id: number;
  spread_amount: string | null;
  medians_by_marketplace: Record<string, number> | null;
  total_listings: number | null;
};

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export function searchProducts(q: string, brand?: string) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (brand) params.set("brand", brand);
  return fetchApi<ProductSearchResult[]>(`/api/v1/search?${params}`);
}

export function getProduct(id: number) {
  return fetchApi<Record<string, unknown>>(`/api/v1/products/${id}`);
}

export function getProductMetrics(id: number) {
  return fetchApi<ProductMetrics>(`/api/v1/products/${id}/metrics`);
}

export function getProductPrices(id: number, range = "90d") {
  return fetchApi<PricePoint[]>(`/api/v1/products/${id}/prices?range=${range}`);
}

export function getMarketplaceCompare(id: number) {
  return fetchApi<MarketplaceCompare>(`/api/v1/products/${id}/marketplaces`);
}

export function getFacets() {
  return fetchApi<{ brands: string[]; conditions: string[]; marketplaces: string[] }>(
    "/api/v1/facets"
  );
}
