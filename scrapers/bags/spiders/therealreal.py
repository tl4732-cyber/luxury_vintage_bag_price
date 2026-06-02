"""
The RealReal handbag listings spider (scrapy-playwright).

Pilot categories: Chanel and Hermès women handbags.
"""

import re

import scrapy
from bags.items import ListingItem
from bags.utils import utc_now
from scrapy_playwright.page import PageMethod


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
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 0.5,
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
    }

    start_urls = [
        "https://www.therealreal.com/designers/chanel/women/handbags",
        "https://www.therealreal.com/designers/hermes/women/handbags",
    ]

    def log_error(self, failure):
        self.logger.error(repr(failure))

    def start_requests(self):
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
        @url https://www.therealreal.com/designers/chanel/women/handbags
        @returns items 0 100
        @returns request 0 20
        @scrapes url title price_amount
        """
        cards = response.css(
            "[data-testid='product-card'], .product-card, .plp-product-card, article a[href*='/products/']"
        )
        if not cards:
            cards = response.css("a[href*='/products/']")

        seen_urls = set()
        for card in cards:
            link = card.css("a::attr(href)").get() or card.attrib.get("href")
            if not link or "/products/" not in link:
                parent_link = card.xpath("ancestor-or-self::a/@href").get()
                link = parent_link
            if not link:
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
            if not title and not price_text:
                yield scrapy.Request(
                    url,
                    callback=self.parse_product,
                    errback=self.log_error,
                    meta={"playwright": True},
                    dont_filter=True,
                )
                continue

            item = self._build_item(url, title, price_text, response.url)
            if item:
                yield item

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
        if not url:
            return None
        price = self._parse_price(price_text)
        if price is None:
            return None

        source_id = url.rstrip("/").split("/")[-1]
        brand = self._brand_from_url(page_url) or self._brand_from_title(title or "")

        item = ListingItem()
        item["marketplace"] = "therealreal"
        item["source_listing_id"] = source_id
        item["url"] = url
        item["title"] = (title or "").strip()
        item["price_amount"] = price
        item["currency"] = "USD"
        item["price_type"] = "ask"
        item["brand"] = brand
        item["model"] = self._model_from_title(title or "")
        item["status"] = "active"
        item["scraped_at"] = utc_now()
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

    def _brand_from_url(self, url: str) -> str | None:
        if "/designers/chanel/" in url:
            return "Chanel"
        if "/designers/hermes/" in url:
            return "Hermès"
        if "/designers/louis-vuitton/" in url:
            return "Louis Vuitton"
        return None

    def _brand_from_title(self, title: str) -> str | None:
        for brand in ("Chanel", "Hermès", "Hermes", "Louis Vuitton", "Gucci", "Prada"):
            if brand.lower() in title.lower():
                return "Hermès" if brand == "Hermes" else brand
        return None

    def _model_from_title(self, title: str) -> str | None:
        patterns = [
            "Classic Flap",
            "Boy Bag",
            "Birkin",
            "Kelly",
            "Speedy",
            "Neverfull",
        ]
        for pattern in patterns:
            if pattern.lower() in title.lower():
                return pattern
        return None
