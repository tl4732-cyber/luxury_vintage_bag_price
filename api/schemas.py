from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class BrandOut(BaseModel):
    id: int
    name: str
    slug: str

    class Config:
        from_attributes = True


class ProductModelOut(BaseModel):
    id: int
    name: str
    slug: str
    brand: BrandOut

    class Config:
        from_attributes = True


class ProductSearchResult(BaseModel):
    id: int
    brand_name: str
    model_name: str
    size: str | None
    median_price: Decimal | None
    active_listing_count: int | None


class ProductMetrics(BaseModel):
    product_id: int
    active_listing_count: int | None
    median_price: Decimal | None
    mean_price: Decimal | None
    min_price: Decimal | None
    max_price: Decimal | None
    p25_price: Decimal | None
    p75_price: Decimal | None


class PricePoint(BaseModel):
    price_date: date
    marketplace: str | None
    median_price: Decimal
    mean_price: Decimal | None
    listing_count: int | None


class MarketplaceCompare(BaseModel):
    product_id: int
    spread_amount: Decimal | None
    highest_marketplace_median: Decimal | None
    lowest_marketplace_median: Decimal | None
    medians_by_marketplace: dict | None
    total_listings: int | None


class FacetsOut(BaseModel):
    brands: list[str]
    conditions: list[str]
    marketplaces: list[str]
