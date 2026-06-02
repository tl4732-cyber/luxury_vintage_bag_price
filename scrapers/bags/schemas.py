from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ListingSchema(BaseModel):
    marketplace: str
    source_listing_id: str
    url: str
    title: str | None = None
    price_amount: float
    currency: str = "USD"
    price_type: Literal["ask", "sold", "auction_current"] = "ask"
    condition_raw: str | None = None
    condition_normalized: str | None = None
    brand: str | None = None
    model: str | None = None
    size: str | None = None
    color: str | None = None
    material: str | None = None
    year: str | None = None
    hardware: str | None = None
    seller_type: str | None = None
    status: Literal["active", "sold", "removed"] = "active"
    scraped_at: datetime | None = None
    content_hash: str | None = None
    image_urls: list[str] = Field(default_factory=list)

    @field_validator("price_amount")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("price_amount must be positive")
        return v

    @field_validator("marketplace")
    @classmethod
    def marketplace_known(cls, v: str) -> str:
        allowed = {"ebay", "therealreal"}
        if v not in allowed:
            raise ValueError(f"marketplace must be one of {allowed}")
        return v
