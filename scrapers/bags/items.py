import scrapy


class ListingItem(scrapy.Item):
    """One handbag listing from a marketplace (filled in by spiders)."""

    marketplace = scrapy.Field()
    source_listing_id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    price_amount = scrapy.Field()
    currency = scrapy.Field()
    condition_raw = scrapy.Field()
    condition_normalized = scrapy.Field()
    status = scrapy.Field()
    scraped_at = scrapy.Field()
    content_hash = scrapy.Field()
    product_variant_id = scrapy.Field()  # set by ProductLinkPipeline
    listing_id = scrapy.Field()  # set by PostgresListingPipeline
    _is_new_listing = scrapy.Field()  # set by PostgresListingPipeline
