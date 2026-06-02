from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.schemas import (
    FacetsOut,
    MarketplaceCompare,
    PricePoint,
    ProductMetrics,
    ProductSearchResult,
)
from db.models import Brand, Listing, ListingStatus, Marketplace, Product, ProductModel
from db.session import get_session_factory

router = APIRouter(prefix="/api/v1")


def get_db():
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/search", response_model=list[ProductSearchResult])
def search_products(
    q: str | None = Query(None, description="Search brand or model name"),
    brand: str | None = None,
    model: str | None = None,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    sql = """
    SELECT
        p.id,
        b.name AS brand_name,
        pm.name AS model_name,
        p.size,
        m.median_price,
        m.active_listing_count
    FROM products p
    JOIN product_models pm ON pm.id = p.product_model_id
    JOIN brands b ON b.id = pm.brand_id
    LEFT JOIN v_product_metrics_current m ON m.product_id = p.id
    WHERE 1=1
    """
    params: dict = {"limit": limit}
    if q:
        sql += " AND (b.name ILIKE :q OR pm.name ILIKE :q)"
        params["q"] = f"%{q}%"
    if brand:
        sql += " AND b.slug = :brand"
        params["brand"] = brand
    if model:
        sql += " AND pm.slug = :model"
        params["model"] = model
    sql += " ORDER BY m.median_price DESC NULLS LAST LIMIT :limit"
    rows = db.execute(text(sql), params).mappings().all()
    return [ProductSearchResult(**row) for row in rows]


@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    pm = db.get(ProductModel, product.product_model_id)
    brand = db.get(Brand, pm.brand_id) if pm else None
    return {
        "id": product.id,
        "size": product.size,
        "material": product.material,
        "hardware_color": product.hardware_color,
        "brand": {"id": brand.id, "name": brand.name, "slug": brand.slug} if brand else None,
        "model": {"id": pm.id, "name": pm.name, "slug": pm.slug} if pm else None,
    }


@router.get("/products/{product_id}/metrics", response_model=ProductMetrics)
def get_product_metrics(product_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT * FROM v_product_metrics_current WHERE product_id = :id"),
        {"id": product_id},
    ).mappings().first()
    if not row:
        raise HTTPException(404, "No metrics for product")
    return ProductMetrics(product_id=product_id, **row)


@router.get("/products/{product_id}/prices", response_model=list[PricePoint])
def get_product_prices(
    product_id: int,
    range: str = Query("90d", pattern="^(7d|30d|90d|365d)$"),
    marketplace: str | None = None,
    db: Session = Depends(get_db),
):
    days = {"7d": 7, "30d": 30, "90d": 90, "365d": 365}[range]
    since = date.today() - timedelta(days=days)
    sql = """
    SELECT price_date, marketplace, median_price, mean_price, listing_count
    FROM v_product_price_daily
    WHERE product_id = :id AND price_date >= :since
    """
    params = {"id": product_id, "since": since}
    if marketplace:
        sql += " AND marketplace = :marketplace"
        params["marketplace"] = marketplace
    sql += " ORDER BY price_date ASC"
    rows = db.execute(text(sql), params).mappings().all()
    return [PricePoint(**row) for row in rows]


@router.get("/products/{product_id}/marketplaces", response_model=MarketplaceCompare)
def compare_marketplaces(product_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT * FROM v_marketplace_spread WHERE product_id = :id"),
        {"id": product_id},
    ).mappings().first()
    if not row:
        raise HTTPException(404, "No marketplace comparison data")
    return MarketplaceCompare(**row)


@router.get("/products/{product_id}/listings")
def list_product_listings(product_id: int, db: Session = Depends(get_db)):
    listings = (
        db.query(Listing)
        .filter(Listing.product_id == product_id, Listing.status == ListingStatus.ACTIVE)
        .limit(50)
        .all()
    )
    result = []
    for listing in listings:
        mp = db.get(Marketplace, listing.marketplace_id)
        latest = db.execute(
            text(
                """
                SELECT price_amount, currency, observed_at
                FROM price_observations
                WHERE listing_id = :lid
                ORDER BY observed_at DESC LIMIT 1
                """
            ),
            {"lid": listing.id},
        ).mappings().first()
        result.append(
            {
                "id": listing.id,
                "marketplace": mp.code if mp else None,
                "url": listing.url,
                "title": listing.title,
                "condition": listing.condition_normalized,
                "latest_price": latest["price_amount"] if latest else None,
                "currency": latest["currency"] if latest else None,
            }
        )
    return result


@router.get("/facets", response_model=FacetsOut)
def get_facets(db: Session = Depends(get_db)):
    brands = [r[0] for r in db.execute(text("SELECT name FROM brands ORDER BY name")).all()]
    conditions = [
        r[0]
        for r in db.execute(
            text(
                "SELECT DISTINCT condition_normalized FROM listings "
                "WHERE condition_normalized IS NOT NULL ORDER BY 1"
            )
        ).all()
    ]
    marketplaces = [
        r[0] for r in db.execute(text("SELECT code FROM marketplaces ORDER BY code")).all()
    ]
    return FacetsOut(brands=brands, conditions=conditions, marketplaces=marketplaces)
