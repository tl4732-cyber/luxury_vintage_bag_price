import unittest

from bags.items import ListingItem
from bags.spiders.ebay_api import EbayApiSpider


class EbayApiSpiderTest(unittest.TestCase):
    def setUp(self):
        self.spider = EbayApiSpider()

    def test_item_from_summary(self):
        summary = {
            "itemId": "v1|123|0",
            "title": "Chanel Classic Flap Medium",
            "price": {"value": "5500.00", "currency": "USD"},
            "itemWebUrl": "https://www.ebay.com/itm/123",
        }
        item = self.spider._item_from_summary(summary)
        self.assertIsInstance(item, ListingItem)
        self.assertEqual(item["marketplace"], "ebay")
        self.assertEqual(item["price_amount"], 5500.0)

    def test_mock_items_count(self):
        items = list(self.spider._mock_items())
        self.assertEqual(len(items), 2)


if __name__ == "__main__":
    unittest.main()
