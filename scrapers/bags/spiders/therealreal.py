"""
Step 5: The RealReal handbag listings spider (scrapy-playwright).

Pilot: Chanel and Hermès women handbags.

Offline test (no browser):
  scrapy crawl therealreal -a use_mock=1 -o out.json

Live scrape (requires playwright install chromium):
  playwright install chromium
  scrapy crawl therealreal -o out.json
"""

import re

import scrapy
from scrapy_playwright.page import PageMethod

from bags.items import ListingItem


class TherealrealSpider(scrapy.Spider):
    name = "therealreal"
    allowed_domains = ["therealreal.com", "www.therealreal.com"]

    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 2,
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
    }

    start_urls = [
        "https://www.therealreal.com/designers/chanel/women/handbags",
        "https://www.therealreal.com/designers/hermes/women/handbags",
    ]

    def __init__(self, use_mock=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_mock = use_mock in (True, "true", "1", 1)

    def log_error(self, failure):
        response = getattr(failure.value, "response", None)
        if response is not None and response.status == 403:
            self.logger.error(
                "The RealReal returned 403 (bot protection / captcha). "
                "Live scraping is blocked from automated browsers. "
                "Use: scrapy crawl therealreal -a use_mock=1 -o out.json "
                "or rely on ebay_api for real marketplace data."
            )
        else:
            self.logger.error(repr(failure))

    async def start(self):
        if self.use_mock:
            self.logger.info("use_mock=1 — yielding sample TRR items (no browser)")
            for item in self._mock_items():
                yield item
            return

        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.log_error,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                },
            )

    def parse(self, response):
        """
        @returns items 0 100
        @returns request 0 20
        @scrapes url title price_amount
        """
        cards = response.css(
            "[data-testid='product-card'], .product-card, .plp-product-card"
        )
        if not cards:
            cards = response.css("a[href*='/products/']")

        seen_urls = set()
        for card in cards:
            link = card.css("a::attr(href)").get() or card.attrib.get("href")
            if not link:
                link = card.xpath("ancestor-or-self::a/@href").get()
            if not link or "/products/" not in link:
                continue

            url = response.urljoin(link)
            if url in seen_urls:
                continue
            seen_urls.add(url)

            title = (
                card.css("[data-testid='product-title']::text").get()
                or card.css(".product-title::text").get()
                or card.css("h2::text").get()
                or card.css("img::attr(alt)").get()
            )
            price_text = (
                card.css("[data-testid='product-price']::text").get()
                or card.css(".price::text").get()
                or card.css("[class*='price']::text").get()
            )

            if title and price_text:
                item = self._build_item(url, title, price_text, response.url)
                if item:
                    yield item
            else:
                yield scrapy.Request(
                    url,
                    callback=self.parse_product,
                    errback=self.log_error,
                    meta={"playwright": True},
                    dont_filter=True,
                )

        next_page = (
            response.css("a[rel='next']::attr(href)").get()
            or response.css(".pagination a.next::attr(href)").get()
            or response.css("[aria-label='Next']::attr(href)").get()
        )
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                callback=self.parse,
                errback=self.log_error,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                },
            )

    def parse_product(self, response):
        title = (
            response.css("h1::text").get()
            or response.css("[data-testid='pdp-title']::text").get()
        )
        price_text = (
            response.css("[data-testid='pdp-price']::text").get()
            or response.css(".price::text").get()
            or response.css("[class*='Price']::text").get()
        )
        condition = response.css("[data-testid='condition']::text").get()
        item = self._build_item(response.url, title, price_text, response.url)
        if item:
            if condition:
                item["condition_raw"] = condition.strip()
            yield item

    def _build_item(self, url, title, price_text, page_url) -> ListingItem | None:
        price = self._parse_price(price_text)
        if not url or price is None:
            return None

        item = ListingItem()
        item["marketplace"] = "therealreal"
        item["source_listing_id"] = url.rstrip("/").split("/")[-1]
        item["url"] = url
        item["title"] = (title or "").strip()
        item["price_amount"] = price
        item["currency"] = "USD"
        return item

    def _parse_price(self, text: str | None) -> float | None:
        if not text:
            return None
        match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
        if not match:
            return None
        try:
            return float(match.group().replace(",", ""))
        except ValueError:
            return None

    def _brand_from_page(self, page_url: str) -> str | None:
        if "/designers/chanel/" in page_url:
            return "Chanel"
        if "/designers/hermes/" in page_url:
            return "Hermès"
        return None

    def _mock_items(self):
        rows = [
            {
                "url": "https://www.therealreal.com/products/mock-chanel-classic-flap",
                "title": "Chanel Lambskin Quilted Classic Double Flap Bag",
                "price_text": "$4,850.00",
                "condition_raw": "Very Good",
            },
            {
                "url": "https://www.therealreal.com/products/mock-hermes-birkin-30",
                "title": "Hermès Togo Birkin 30 Gold",
                "price_text": "$18,200.00",
                "condition_raw": "Excellent",
            },
        ]
        for row in rows:
            item = self._build_item(
                row["url"], row["title"], row["price_text"], row["url"]
            )
            if item:
                item["condition_raw"] = row["condition_raw"]
                yield item
