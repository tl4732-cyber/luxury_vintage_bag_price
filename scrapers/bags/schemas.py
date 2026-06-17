from typing import Literal

from pydantic import BaseModel, Field, field_validator
# Pydantic for defining, validating, and converting data.


class ListingSchema(BaseModel): 
    marketplace: str
    source_listing_id: str
    url: str
    title: str | None = None
    price_amount: float
    currency: str = "USD"
    condition_raw: str | None = None
    condition_normalized: str | None = None
    status: Literal["active", "sold", "removed"] = "active"

    @field_validator("marketplace") 
    @classmethod 
    def marketplace_allowed(cls, value: str) -> str:
        allowed = {"ebay", "therealreal"}
        if value not in allowed:
            raise ValueError(f"marketplace must be one of {allowed}")
        return value

    @field_validator("price_amount") 
    @classmethod 
    def price_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("price_amount must be greater than 0")
        return value

    @field_validator("url")
    @classmethod
    def url_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("url is required")
        return value

    @field_validator("source_listing_id")
    @classmethod
    def source_id_not_empty(cls, value: str) -> str:
        if not str(value).strip():
            raise ValueError("source_listing_id is required")
        return str(value)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, value: str) -> str:
        return (value or "USD").upper()[:3]
