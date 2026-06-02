import unittest

from scrapy.http import HtmlResponse, TextResponse

from bags.spiders.ebay_api import EbayApiSpider
from bags.items import ListingItem


class EbayApiSpiderTest(unittest.TestCase):
    def setUp(self):
        self.spider = EbayApiSpider()

    def test_item_from_summary(self):
        summary = {
            "itemId": "v1|123|0",
            "title": "Chanel Classic Flap Medium",
            "price": {"value": "5500.00", "currency": "USD"},
            "itemWebUrl": "https://www.ebay.com/itm/123",
            "condition": "Pre-owned",
        }
        item = self.spider._item_from_summary(summary)
        self.assertIsInstance(item, ListingItem)
        self.assertEqual(item["marketplace"], "ebay")
        self.assertEqual(item["source_listing_id"], "v1|123|0")
        self.assertEqual(item["price_amount"], 5500.0)
        self.assertEqual(item["brand"], "Chanel")

    def test_extract_brand_hermes(self):
        self.assertEqual(
            self.spider._extract_brand("Authentic Hermes Birkin 30"),
            "Hermès",
        )

    def test_mock_items_when_no_credentials(self):
        items = list(self.spider._mock_items())
        self.assertGreaterEqual(len(items), 2)


if __name__ == "__main__":
    unittest.main()
