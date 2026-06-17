"""
Step 3: eBay Browse API spider.

Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET in .env (see .env.example).
Without credentials, yields two eBay-shaped mock items so you can still test export.
"""

import base64 # encode your client ID and secret for OAuth
import os #reads environment variables like EBAY_CLIENT_ID
from urllib.parse import urlencode #converts a dictionary into a URL query string

import scrapy

from bags.items import ListingItem


class EbayApiSpider(scrapy.Spider):
    name = "ebay_api"
    allowed_domains = ["api.ebay.com", "api.sandbox.ebay.com"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_DELAY": 0.5,
    }

    DEFAULT_QUERIES = [
        "Chanel classic flap handbag",
        "Hermes Birkin bag",
    ]

    def __init__(self, query=None, limit=25, category_id=None, paginate=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_queries = [query] if query else self.DEFAULT_QUERIES
        self.limit = int(limit)
        self.category_id = category_id  # e.g. 169291; omit on sandbox (little test data)
        self.paginate = paginate in (True, "true", "1", 1)
        self._token = None
        self._items_yielded = 0

    @property  
    def api_base(self): 
        if os.getenv("EBAY_ENV", "sandbox") == "production":
            return "https://api.ebay.com"
        return "https://api.sandbox.ebay.com"

    def log_error(self, failure):
        self.logger.error(repr(failure))

    async def start(self):
        client_id = os.getenv("EBAY_CLIENT_ID", "")
        client_secret = os.getenv("EBAY_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            self.logger.warning(
                "No eBay credentials in .env — yielding mock eBay items. "
                "Copy .env.example to .env and add EBAY_CLIENT_ID / EBAY_CLIENT_SECRET."
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
            self.logger.error("eBay OAuth failed: %s", data) 
            return 

        for query in self.search_queries: 
            query_params = {
                "q": query,
                "limit": self.limit,
                "filter": "buyingOptions:{FIXED_PRICE}",
            }
            if self.category_id:
                query_params["category_ids"] = self.category_id 
            params = urlencode(query_params)
            yield scrapy.Request(
                f"{self.api_base}/buy/browse/v1/item_summary/search?{params}", 
                headers={ 
                    "Authorization": f"Bearer {self._token}",
                    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                }, 
                callback=self.parse_search,
                errback=self.log_error, 
            )

    #parse the response from the eBay Browse API
    def parse_search(self, response): 
        """
        @returns items 0 50
        @scrapes source_listing_id title price_amount
        """
        data = response.json() 
        summaries = data.get("itemSummaries") or []
        if not summaries: 
            self.logger.warning( 
                "eBay returned 0 items for this query (total=%s). "
                "Sandbox has almost no luxury listings — use EBAY_ENV=production "
                "with production keys for real Chanel results.",
                data.get("total", 0), 
            )
        for summary in summaries:
            if self._items_yielded >= self.limit:
                return
            self._items_yielded += 1 
            yield self._item_from_summary(summary) 

        if not self.paginate:
            return

        next_url = data.get("next")
        if isinstance(next_url, str) and self._token and self._items_yielded < self.limit:
            yield scrapy.Request( 
                next_url, 
                headers={ 
                    "Authorization": f"Bearer {self._token}",
                    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                },
                callback=self.parse_search, 
                errback=self.log_error,  
            )

    def _item_from_summary(self, summary: dict) -> ListingItem: 
        price_block = summary.get("price") or {}
        item = ListingItem()
        item["marketplace"] = "ebay"
        item["source_listing_id"] = summary.get("itemId", "")
        item["url"] = summary.get("itemWebUrl", "")
        item["title"] = summary.get("title", "")
        item["price_amount"] = float(price_block.get("value", 0))
        item["currency"] = price_block.get("currency", "USD")
        item["condition_raw"] = summary.get("condition")
        return item

    def _mock_items(self): 
        mocks = [
            {
                "itemId": "v1|mock_chanel|0",
                "title": "Chanel Classic Flap Medium Black Caviar",
                "price": {"value": "6500.00", "currency": "USD"},
                "itemWebUrl": "https://www.ebay.com/itm/mock_chanel",
            },
            {
                "itemId": "v1|mock_hermes|0",
                "title": "Hermes Birkin 30 Togo Gold Hardware",
                "price": {"value": "18500.00", "currency": "USD"},
                "itemWebUrl": "https://www.ebay.com/itm/mock_hermes",
            },
        ]
        for summary in mocks:
            yield self._item_from_summary(summary)
