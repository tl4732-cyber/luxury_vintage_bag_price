"""
eBay Browse API spider for luxury handbag listings.

Requires EBAY_CLIENT_ID and EBAY_CLIENT_SECRET in environment.
Sandbox: https://api.sandbox.ebay.com | Production: https://api.ebay.com
"""

import base64
import os
from urllib.parse import urlencode

import scrapy
from bags.items import ListingItem
from bags.utils import utc_now


class EbayApiSpider(scrapy.Spider):
    name = "ebay_api"
    allowed_domains = ["api.ebay.com", "api.sandbox.ebay.com"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_DELAY": 0.5,
        "ITEM_PIPELINES": {
            "bags.pipelines.ValidationPipeline": 100,
            "bags.pipelines.NormalizationPipeline": 200,
            "bags.pipelines.ScrapeRunPipeline": 250,
            "bags.pipelines.PostgresListingPipeline": 300,
            "bags.pipelines.PriceObservationPipeline": 400,
            "bags.pipelines.ProductMatchingPipeline": 500,
        },
    }

    SEARCH_QUERIES = [
        "Chanel classic flap handbag",
        "Hermes Birkin bag",
        "Louis Vuitton speedy handbag",
    ]

    def __init__(self, query=None, limit=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_queries = [query] if query else self.SEARCH_QUERIES
        self.limit = int(limit)
        self._token = None

    @property
    def api_base(self):
        env = os.environ.get("EBAY_ENV", "sandbox")
        if env == "production":
            return "https://api.ebay.com"
        return "https://api.sandbox.ebay.com"

    def log_error(self, failure):
        self.logger.error(repr(failure))

    def start_requests(self):
        client_id = os.environ.get("EBAY_CLIENT_ID", "")
        client_secret = os.environ.get("EBAY_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            self.logger.warning(
                "EBAY_CLIENT_ID/EBAY_CLIENT_SECRET not set — yielding mock items for dev"
            )
            for item in self._mock_items():
                yield item
            return

        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        yield scrapy.Request(
            f"{self.api_base}/identity/v1/oauth2/token",
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {credentials}",
            },
            body="grant_type=client_credentials&scope=https://api.ebay.com/oauth/api_scope",
            callback=self.parse_token,
            errback=self.log_error,
            dont_filter=True,
        )

    def parse_token(self, response):
        data = response.json()
        self._token = data.get("access_token")
        if not self._token:
            self.logger.error("Failed to obtain eBay OAuth token: %s", data)
            return
        for query in self.search_queries:
            params = urlencode(
                {
                    "q": query,
                    "limit": self.limit,
                    "category_ids": "169291",
                    "filter": "buyingOptions:{FIXED_PRICE}",
                }
            )
            yield scrapy.Request(
                f"{self.api_base}/buy/browse/v1/item_summary/search?{params}",
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                },
                callback=self.parse_search,
                errback=self.log_error,
                meta={"query": query},
            )

    def parse_search(self, response):
        """
        @returns items 0 50
        @scrapes source_listing_id title price_amount
        """
        data = response.json()
        for summary in data.get("itemSummaries", []):
            yield self._item_from_summary(summary)

        next_link = None
        for link in data.get("refinement", {}).get("navigation", []) or []:
            pass
        for link in data.get("links", []) or []:
            if link.get("rel") == "next":
                next_link = link.get("href")
                break
        if not next_link:
            for link in data.get("href") or []:
                pass
        next_href = data.get("next")
        if next_href:
            yield scrapy.Request(
                next_href,
                headers={"Authorization": f"Bearer {self._token}"},
                callback=self.parse_search,
                errback=self.log_error,
            )

    def _item_from_summary(self, summary: dict) -> ListingItem:
        item_id = summary.get("itemId", "")
        price_block = summary.get("price") or {}
        value = price_block.get("value", "0")
        item = ListingItem()
        item["marketplace"] = "ebay"
        item["source_listing_id"] = item_id
        item["url"] = summary.get("itemWebUrl", "")
        item["title"] = summary.get("title", "")
        item["price_amount"] = float(value)
        item["currency"] = price_block.get("currency", "USD")
        item["price_type"] = "ask"
        item["condition_raw"] = (summary.get("condition") or summary.get("conditionId", ""))
        item["brand"] = self._extract_brand(summary.get("title", ""))
        item["model"] = None
        item["status"] = "active"
        item["scraped_at"] = utc_now()
        images = summary.get("thumbnailImages") or []
        item["image_urls"] = [i.get("imageUrl") for i in images if i.get("imageUrl")]
        if summary.get("image", {}).get("imageUrl"):
            item["image_urls"].insert(0, summary["image"]["imageUrl"])
        return item

    def _extract_brand(self, title: str) -> str | None:
        brands = ["Chanel", "Hermès", "Hermes", "Louis Vuitton", "Gucci", "Prada"]
        for brand in brands:
            if brand.lower() in title.lower():
                return "Hermès" if brand == "Hermes" else brand
        return None

    def _mock_items(self):
        """Dev fallback when API credentials are absent."""
        mocks = [
            {
                "itemId": "v1|mock_chanel_001|0",
                "title": "Chanel Classic Flap Medium Black Caviar",
                "price": {"value": "6500.00", "currency": "USD"},
                "itemWebUrl": "https://www.ebay.com/itm/mock_chanel_001",
                "condition": "Pre-owned",
            },
            {
                "itemId": "v1|mock_hermes_001|0",
                "title": "Hermes Birkin 30 Togo Gold Hardware",
                "price": {"value": "18500.00", "currency": "USD"},
                "itemWebUrl": "https://www.ebay.com/itm/mock_hermes_001",
                "condition": "Pre-owned",
            },
        ]
        for summary in mocks:
            yield self._item_from_summary(summary)
