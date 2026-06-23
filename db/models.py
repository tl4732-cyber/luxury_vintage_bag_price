import enum
from datetime import datetime

from sqlalchemy import (
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


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class Marketplace(Base):
    __tablename__ = "marketplaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    models: Mapped[list["Model"]] = relationship(back_populates="brand")


class Model(Base):
    __tablename__ = "models"
    __table_args__ = (UniqueConstraint("brand_id", "name", name="uq_model_brand_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    brand: Mapped["Brand"] = relationship(back_populates="models")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="model")


class ProductVariant(Base):
    """One physical configuration: model + size + color + leather."""

    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint(
            "model_id",
            "size",
            "color",
            "leather",
            name="uq_variant_identity",
        ),
        Index("ix_variants_model_id", "model_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    size: Mapped[str | None] = mapped_column(String(32))
    color: Mapped[str | None] = mapped_column(String(64))
    leather: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    model: Mapped["Model"] = relationship(back_populates="variants")
    listings: Mapped[list["Listing"]] = relationship(back_populates="product_variant")


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("marketplace_id", "source_listing_id", name="uq_listing_marketplace_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_id: Mapped[int] = mapped_column(ForeignKey("marketplaces.id"), nullable=False)
    source_listing_id: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    condition_raw: Mapped[str | None] = mapped_column(String(128))
    condition_normalized: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus, name="listing_status", values_callable=_enum_values),
        default=ListingStatus.ACTIVE,
    )
    content_hash: Mapped[str | None] = mapped_column(String(64))
    product_variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    marketplace: Mapped["Marketplace"] = relationship()
    product_variant: Mapped["ProductVariant | None"] = relationship(back_populates="listings")
    price_observations: Mapped[list["PriceObservation"]] = relationship(back_populates="listing")


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
        Enum(PriceType, name="price_type", values_callable=_enum_values),
        default=PriceType.ASK,
    )

    listing: Mapped["Listing"] = relationship(back_populates="price_observations")
