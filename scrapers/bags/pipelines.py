from datetime import datetime, timezone

from itemadapter import ItemAdapter
from pydantic import ValidationError
from scrapy.exceptions import DropItem
from sqlalchemy import select

from bags.product_linking import should_link_listing
from bags.product_matching import get_or_create_variant
from bags.schemas import ListingSchema
from bags.title_parser import parse_title
from bags.utils import compute_content_hash, normalize_condition, utc_now
from db.models import Listing, ListingStatus, Marketplace, PriceObservation, PriceType
from db.session import get_session_factory

# convert scraped timestamps into Python datetime objects
def _parse_scraped_at(value) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return utc_now()


class ValidationPipeline:
    """Drop items missing required fields or with invalid values."""
    # uses a Pydantic model ListingSchema to validate the item

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        try:
            validated = ListingSchema(**adapter.asdict())
            adapter.update(validated.model_dump())
        except ValidationError as exc:

            spider.logger.warning("Dropped invalid item: %s", exc)
            raise DropItem(f"Validation failed: {exc}") from exc
        return item


class NormalizationPipeline:
    """Clean and enrich items before export or database storage."""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if adapter.get("title"):
            adapter["title"] = adapter["title"].strip()
        adapter["currency"] = (adapter.get("currency") or "USD").upper()
        adapter["condition_normalized"] = normalize_condition(adapter.get("condition_raw"))
        if not adapter.get("status"):
            adapter["status"] = "active"
        if not adapter.get("scraped_at"):
            adapter["scraped_at"] = utc_now().isoformat()
        adapter["content_hash"] = compute_content_hash(adapter.asdict())
        return item


class ProductLinkPipeline:
    """Parse title into brand/model attributes and resolve a product variant row."""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        title = adapter.get("title")
        price_amount = adapter.get("price_amount")
        parsed = parse_title(title)

        if not should_link_listing(title, price_amount, parsed):
            adapter["product_variant_id"] = None
            return item

        Session = get_session_factory()
        with Session() as session:
            variant = get_or_create_variant(session, parsed)
            adapter["product_variant_id"] = variant.id
            session.commit()
        return item


class PostgresListingPipeline:
    """Upsert listing row; set listing_id on the item for price pipeline."""

    def __init__(self):
        self.session = None
        self._marketplace_ids: dict[str, int] = {}

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self, spider):
        Session = get_session_factory()
        self.session = Session()
        rows = self.session.execute(select(Marketplace)).scalars().all()
        self._marketplace_ids = {row.code: row.id for row in rows}

    def close_spider(self, spider):
        if self.session:
            self.session.close()

    def _marketplace_id(self, code: str) -> int:
        if code not in self._marketplace_ids:
            mp = Marketplace(code=code, name=code.title())
            self.session.add(mp)
            self.session.flush()
            self._marketplace_ids[code] = mp.id
        return self._marketplace_ids[code]

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        try:
            marketplace_id = self._marketplace_id(adapter["marketplace"])
            source_id = str(adapter["source_listing_id"])
            now = utc_now()

            listing = self.session.execute(
                select(Listing).where(
                    Listing.marketplace_id == marketplace_id,
                    Listing.source_listing_id == source_id,
                )
            ).scalar_one_or_none()

            is_new = listing is None
            if listing is None:
                listing = Listing(
                    marketplace_id=marketplace_id,
                    source_listing_id=source_id,
                    url=adapter["url"],
                    first_seen_at=now,
                )
                self.session.add(listing)

            listing.url = adapter["url"]
            listing.title = adapter.get("title")
            listing.condition_raw = adapter.get("condition_raw")
            listing.condition_normalized = adapter.get("condition_normalized")
            listing.status = ListingStatus(adapter.get("status", "active"))
            listing.content_hash = adapter.get("content_hash")
            listing.product_variant_id = adapter.get("product_variant_id")
            listing.last_seen_at = now
            self.session.flush()

            adapter["listing_id"] = listing.id
            adapter["_is_new_listing"] = is_new
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return item


class PriceObservationPipeline:
    """Append price row only when price changed (or first time seen)."""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        listing_id = adapter.get("listing_id")
        if not listing_id:
            raise DropItem("listing_id missing — run PostgresListingPipeline first")

        Session = get_session_factory()
        with Session() as session:
            last = session.execute(
                select(PriceObservation)
                .where(PriceObservation.listing_id == listing_id)
                .order_by(PriceObservation.observed_at.desc())
                .limit(1)
            ).scalar_one_or_none()

            price_amount = float(adapter["price_amount"])
            currency = adapter.get("currency", "USD")
            should_insert = True
            if last:
                same = float(last.price_amount) == price_amount and last.currency == currency
                should_insert = not same or adapter.get("_is_new_listing")

            if should_insert:
                session.add(
                    PriceObservation(
                        listing_id=listing_id,
                        observed_at=_parse_scraped_at(adapter.get("scraped_at")),
                        price_amount=price_amount,
                        currency=currency,
                        price_type=PriceType.ASK,
                    )
                )
                session.commit()
        return item
