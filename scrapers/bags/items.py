import scrapy


class ListingItem(scrapy.Item):
    """Normalized marketplace listing from any spider."""

    marketplace = scrapy.Field()
    source_listing_id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    price_amount = scrapy.Field()
    currency = scrapy.Field()
    price_type = scrapy.Field()
    condition_raw = scrapy.Field()
    condition_normalized = scrapy.Field()
    brand = scrapy.Field()
    model = scrapy.Field()
    size = scrapy.Field()
    color = scrapy.Field()
    material = scrapy.Field()
    year = scrapy.Field()
    hardware = scrapy.Field()
    seller_type = scrapy.Field()
    status = scrapy.Field()
    scraped_at = scrapy.Field()
    content_hash = scrapy.Field()
    image_urls = scrapy.Field()
    raw_payload = scrapy.Field()


class SoldListingItem(ListingItem):
    """Listing that has sold — final price capture."""

    is_sale = scrapy.Field()
