from datetime import datetime, timezone

from itemadapter import ItemAdapter
from pydantic import ValidationError
from scrapy.exceptions import DropItem
from sqlalchemy import select
from sqlalchemy.orm import Session

from bags.schemas import ListingSchema
from bags.utils import compute_content_hash, normalize_condition, utc_now
from db.models import (
    Listing,
    ListingStatus,
    Marketplace,
    PriceObservation,
    PriceType,
    ScrapeRun,
)
from db.product_matching import match_listing_to_product
from db.session import get_session_factory


class ValidationPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        try:
            validated = ListingSchema(**adapter.asdict())
            adapter.update(validated.model_dump())
        except ValidationError as exc:
            raise DropItem(f"Validation failed: {exc}") from exc
        return item


class NormalizationPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if not adapter.get("scraped_at"):
            adapter["scraped_at"] = utc_now()
        adapter["condition_normalized"] = normalize_condition(
            adapter.get("condition_raw") or adapter.get("condition_normalized")
        )
        adapter["content_hash"] = compute_content_hash(adapter.asdict())
        return item


class ScrapeRunPipeline:
    """Track scrape run metadata per spider execution."""

    def __init__(self):
        self.run_id = None
        self.items_seen = 0
        self.items_new = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self, spider):
        Session = get_session_factory()
        self.session = Session()
        run = ScrapeRun(spider_name=spider.name, status="running")
        self.session.add(run)
        self.session.commit()
        self.run_id = run.id
        spider.scrape_run_id = self.run_id

    def close_spider(self, spider):
        if self.run_id and self.session:
            run = self.session.get(ScrapeRun, self.run_id)
            if run:
                run.finished_at = datetime.now(timezone.utc)
                run.status = "completed"
                run.items_seen = self.items_seen
                run.items_new = getattr(spider, "_items_new", self.items_new)
            self.session.commit()
            self.session.close()

    def process_item(self, item, spider):
        self.items_seen += 1
        return item

    def note_new_listing(self):
        self.items_new += 1


class PostgresListingPipeline:
    def __init__(self):
        self.session: Session | None = None
        self._marketplace_cache: dict[str, int] = {}

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self, spider):
        Session = get_session_factory()
        self.session = Session()
        self._load_marketplaces()

    def close_spider(self, spider):
        if self.session:
            self.session.close()

    def _load_marketplaces(self):
        rows = self.session.execute(select(Marketplace)).scalars().all()
        self._marketplace_cache = {m.code: m.id for m in rows}

    def _marketplace_id(self, code: str) -> int:
        if code not in self._marketplace_cache:
            mp = Marketplace(code=code, name=code.title(), base_url=f"https://{code}.com")
            self.session.add(mp)
            self.session.flush()
            self._marketplace_cache[code] = mp.id
        return self._marketplace_cache[code]

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        marketplace_id = self._marketplace_id(adapter["marketplace"])
        source_id = str(adapter["source_listing_id"])

        listing = self.session.execute(
            select(Listing).where(
                Listing.marketplace_id == marketplace_id,
                Listing.source_listing_id == source_id,
            )
        ).scalar_one_or_none()

        status = ListingStatus(adapter.get("status", "active"))
        now = utc_now()
        is_new = listing is None

        if listing is None:
            listing = Listing(
                marketplace_id=marketplace_id,
                source_listing_id=source_id,
                url=adapter["url"],
                first_seen_at=now,
            )
            self.session.add(listing)
            spider._items_new = getattr(spider, "_items_new", 0) + 1

        listing.url = adapter["url"]
        listing.title = adapter.get("title")
        listing.condition_raw = adapter.get("condition_raw")
        listing.condition_normalized = adapter.get("condition_normalized")
        listing.seller_type = adapter.get("seller_type")
        listing.status = status
        listing.brand_raw = adapter.get("brand")
        listing.model_raw = adapter.get("model")
        listing.last_seen_at = now
        listing.content_hash = adapter.get("content_hash")
        self.session.flush()

        adapter["listing_id"] = listing.id
        adapter["_is_new_listing"] = is_new
        adapter["_listing"] = listing
        self.session.commit()
        return item


class PriceObservationPipeline:
    def __init__(self):
        self.session: Session | None = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        listing_id = adapter.get("listing_id")
        if not listing_id:
            raise DropItem("listing_id missing — PostgresListingPipeline must run first")

        SessionFactory = get_session_factory()
        with SessionFactory() as session:
            last_obs = session.execute(
                select(PriceObservation)
                .where(PriceObservation.listing_id == listing_id)
                .order_by(PriceObservation.observed_at.desc())
                .limit(1)
            ).scalar_one_or_none()

            price_amount = float(adapter["price_amount"])
            currency = adapter.get("currency", "USD")
            price_type = PriceType(adapter.get("price_type", "ask"))

            should_insert = True
            if last_obs:
                same_price = (
                    float(last_obs.price_amount) == price_amount
                    and last_obs.currency == currency
                    and last_obs.price_type == price_type
                )
                should_insert = not same_price or adapter.get("_is_new_listing")

            if should_insert:
                session.add(
                    PriceObservation(
                        listing_id=listing_id,
                        observed_at=adapter.get("scraped_at") or utc_now(),
                        price_amount=price_amount,
                        currency=currency,
                        price_type=price_type,
                        is_sale=price_type == PriceType.SOLD,
                        raw_price_text=str(adapter.get("price_amount")),
                    )
                )
            listing = session.get(Listing, listing_id)
            if listing:
                session.merge(listing)
            session.commit()

        return item


class ProductMatchingPipeline:
    AUTO_MATCH_THRESHOLD = 0.7

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        listing_id = adapter.get("listing_id")
        if not listing_id:
            return item

        SessionFactory = get_session_factory()
        with SessionFactory() as session:
            listing = session.get(Listing, listing_id)
            if not listing or listing.product_id:
                return item

            result = match_listing_to_product(session, listing)
            if result.product_id and result.confidence >= self.AUTO_MATCH_THRESHOLD:
                listing.product_id = result.product_id
                listing.match_confidence = result.confidence
            else:
                listing.match_confidence = result.confidence
            session.commit()

        return item
