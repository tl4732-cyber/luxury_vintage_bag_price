"""
Step 2: mock spider — no network, no API keys.

Yields two sample handbag listings so you can test Scrapy export before eBay/TRR.
"""

import scrapy

from bags.items import ListingItem


class DevSampleSpider(scrapy.Spider):
    name = "dev_sample"

    async def start(self):
        """
        @returns items 2 2
        @scrapes marketplace title price_amount
        """
        for row in self._sample_rows():
            item = ListingItem()
            item["marketplace"] = row["marketplace"]
            item["source_listing_id"] = row["source_listing_id"]
            item["url"] = row["url"]
            item["title"] = row["title"]
            item["price_amount"] = row["price_amount"]
            item["currency"] = row["currency"]
            item["condition_raw"] = row.get("condition_raw")
            yield item

    def _sample_rows(self):
        return [
            {
                "marketplace": "ebay",
                "source_listing_id": "mock-chanel-001",
                "url": "https://www.ebay.com/itm/mock-chanel-001",
                "title": "Chanel Classic Flap Medium Black Caviar",
                "price_amount": 6500.0,
                "currency": "USD",
                "condition_raw": "Pre-owned",
            },
            {
                "marketplace": "therealreal",
                "source_listing_id": "mock-hermes-001",
                "url": "https://www.therealreal.com/products/mock-hermes-001",
                "title": "Hermès Birkin 30 Togo Gold Hardware",
                "price_amount": 18500.0,
                "currency": "USD",
                "condition_raw": "Very Good",
            },
        ]
