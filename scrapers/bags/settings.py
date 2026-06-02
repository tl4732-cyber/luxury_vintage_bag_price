import os
import sys

# Allow imports from project root (db package)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

BOT_NAME = "bags"

SPIDER_MODULES = ["bags.spiders"]
NEWSPIDER_MODULE = "bags.spiders"

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5

USER_AGENT = (
    "LuxuryVintageBagPriceBot/1.0 (+https://github.com/tl4732-cyber/luxury_vintage_bag_price)"
)

ITEM_PIPELINES = {
    "bags.pipelines.ValidationPipeline": 100,
    "bags.pipelines.NormalizationPipeline": 200,
    "bags.pipelines.ScrapeRunPipeline": 250,
    "bags.pipelines.PostgresListingPipeline": 300,
    "bags.pipelines.PriceObservationPipeline": 400,
    "bags.pipelines.ProductMatchingPipeline": 500,
}

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://lvbp:lvbp_dev@localhost:5432/luxury_bags",
)

EBAY_CLIENT_ID = os.environ.get("EBAY_CLIENT_ID", "")
EBAY_CLIENT_SECRET = os.environ.get("EBAY_CLIENT_SECRET", "")
EBAY_ENV = os.environ.get("EBAY_ENV", "sandbox")

FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = os.environ.get("SCRAPY_LOG_LEVEL", "INFO")
LOG_FILE = "bag_scraper.log"

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [429, 500, 502, 503, 504]

# scrapy-playwright (The RealReal spider)
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
