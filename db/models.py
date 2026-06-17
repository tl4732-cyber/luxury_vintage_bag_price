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


class Marketplace(Base):
    __tablename__ = "marketplaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)


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
        Enum(ListingStatus, name="listing_status"), default=ListingStatus.ACTIVE
    )
    content_hash: Mapped[str | None] = mapped_column(String(64))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    marketplace: Mapped["Marketplace"] = relationship() 
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
        Enum(PriceType, name="price_type"), default=PriceType.ASK
    )

    listing: Mapped["Listing"] = relationship(back_populates="price_observations")
