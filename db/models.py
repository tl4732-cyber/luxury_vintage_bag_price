import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ListingStatus(str, enum.Enum):
    ACTIVE = "active"
    SOLD = "sold"
    REMOVED = "removed"


class PriceType(str, enum.Enum):
    ASK = "ask"
    SOLD = "sold"
    AUCTION_CURRENT = "auction_current"


class AttributeSource(str, enum.Enum):
    NORMALIZED = "normalized"
    RAW = "raw"


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    product_models: Mapped[list["ProductModel"]] = relationship(back_populates="brand")


class ProductModel(Base):
    __tablename__ = "product_models"
    __table_args__ = (UniqueConstraint("brand_id", "slug", name="uq_product_model_brand_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str | None] = mapped_column(String(64))
    default_size: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    brand: Mapped["Brand"] = relationship(back_populates="product_models")
    products: Mapped[list["Product"]] = relationship(back_populates="product_model")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_model_id: Mapped[int] = mapped_column(
        ForeignKey("product_models.id"), nullable=False
    )
    size: Mapped[str | None] = mapped_column(String(64))
    material: Mapped[str | None] = mapped_column(String(128))
    hardware_color: Mapped[str | None] = mapped_column(String(64))
    style_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    product_model: Mapped["ProductModel"] = relationship(back_populates="products")
    attributes: Mapped[list["ProductAttribute"]] = relationship(back_populates="product")
    listings: Mapped[list["Listing"]] = relationship(back_populates="product")


class ProductAttribute(Base):
    __tablename__ = "product_attributes"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    attr_key: Mapped[str] = mapped_column(String(64), nullable=False)
    attr_value: Mapped[str] = mapped_column(String(256), nullable=False)
    source: Mapped[AttributeSource] = mapped_column(
        Enum(AttributeSource, name="attribute_source"), default=AttributeSource.RAW
    )

    product: Mapped["Product"] = relationship(back_populates="attributes")


class ProductAlias(Base):
    __tablename__ = "product_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    alias_text: Mapped[str] = mapped_column(String(512), nullable=False)
    marketplace_id: Mapped[int | None] = mapped_column(ForeignKey("marketplaces.id"))

    product: Mapped["Product"] = relationship()


class Marketplace(Base):
    __tablename__ = "marketplaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    base_url: Mapped[str] = mapped_column(String(256), nullable=False)

    listings: Mapped[list["Listing"]] = relationship(back_populates="marketplace")


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint(
            "marketplace_id", "source_listing_id", name="uq_listing_marketplace_source"
        ),
        Index("ix_listings_product_id", "product_id"),
        Index("ix_listings_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_id: Mapped[int] = mapped_column(ForeignKey("marketplaces.id"), nullable=False)
    source_listing_id: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    title: Mapped[str | None] = mapped_column(Text)
    condition_raw: Mapped[str | None] = mapped_column(String(128))
    condition_normalized: Mapped[str | None] = mapped_column(String(64))
    seller_type: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus, name="listing_status"), default=ListingStatus.ACTIVE
    )
    brand_raw: Mapped[str | None] = mapped_column(String(128))
    model_raw: Mapped[str | None] = mapped_column(String(256))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    content_hash: Mapped[str | None] = mapped_column(String(64))
    match_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))

    marketplace: Mapped["Marketplace"] = relationship(back_populates="listings")
    product: Mapped["Product | None"] = relationship(back_populates="listings")
    price_observations: Mapped[list["PriceObservation"]] = relationship(
        back_populates="listing"
    )


class PriceObservation(Base):
    __tablename__ = "price_observations"
    __table_args__ = (Index("ix_price_obs_listing_observed", "listing_id", "observed_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    price_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    price_type: Mapped[PriceType] = mapped_column(
        Enum(PriceType, name="price_type"), default=PriceType.ASK
    )
    is_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_price_text: Mapped[str | None] = mapped_column(String(64))

    listing: Mapped["Listing"] = relationship(back_populates="price_observations")


class ListingSnapshot(Base):
    __tablename__ = "listing_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    spider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="running")
    items_seen: Mapped[int] = mapped_column(default=0)
    items_new: Mapped[int] = mapped_column(default=0)
    errors_count: Mapped[int] = mapped_column(default=0)


class SocialMention(Base):
    """Phase 4: Reddit / Instagram sentiment ingest."""

    __tablename__ = "social_mentions"
    __table_args__ = (
        UniqueConstraint("platform", "source_id", name="uq_social_platform_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    brand_raw: Mapped[str | None] = mapped_column(String(128))
    model_raw: Mapped[str | None] = mapped_column(String(256))
    text_content: Mapped[str | None] = mapped_column(Text)
    sentiment_score: Mapped[float | None] = mapped_column(Numeric(6, 4))
    engagement_count: Mapped[int | None] = mapped_column(BigInteger)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
