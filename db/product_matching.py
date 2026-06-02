"""Rule-based product matching for listings (Phase 2)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Brand, Listing, Product, ProductAlias, ProductModel


@dataclass
class MatchResult:
    product_id: int | None
    confidence: float
    reason: str


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())


def match_listing_to_product(session: Session, listing: Listing) -> MatchResult:
    """
    Attempt to link a listing to a catalog product.
    High confidence: exact alias hit. Medium: brand+model slug. Low: brand only.
    """
    title = _normalize_text(listing.title)
    brand_raw = _normalize_text(listing.brand_raw)
    model_raw = _normalize_text(listing.model_raw)

    if not brand_raw and not model_raw:
        return MatchResult(None, 0.0, "missing_brand_model")

    search_text = f"{title} {brand_raw} {model_raw}".strip()

    alias_stmt = select(ProductAlias).where(
        ProductAlias.alias_text.ilike(f"%{search_text[:120]}%")
    )
    alias = session.execute(alias_stmt).scalars().first()
    if alias:
        return MatchResult(alias.product_id, 0.95, "alias_match")

    if brand_raw and model_raw:
        brand_slug = slugify(brand_raw)
        model_slug = slugify(model_raw)
        stmt = (
            select(Product.id)
            .join(ProductModel, Product.product_model_id == ProductModel.id)
            .join(Brand, ProductModel.brand_id == Brand.id)
            .where(Brand.slug == brand_slug, ProductModel.slug == model_slug)
            .limit(1)
        )
        product_id = session.execute(stmt).scalar_one_or_none()
        if product_id:
            return MatchResult(product_id, 0.75, "brand_model_slug")

    if brand_raw:
        brand_slug = slugify(brand_raw)
        brand = session.execute(
            select(Brand).where(Brand.slug == brand_slug)
        ).scalar_one_or_none()
        if brand:
            return MatchResult(None, 0.35, "brand_only_no_model")

    return MatchResult(None, 0.0, "no_match")
