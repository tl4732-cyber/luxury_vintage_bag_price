import unittest

from scrapy.exceptions import DropItem

from bags.items import ListingItem
from bags.pipelines import NormalizationPipeline, ValidationPipeline


class _FakeSpider:
    name = "test"
    logger = type("L", (), {"warning": lambda *a, **k: None})()


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.spider = _FakeSpider()
        self.validation = ValidationPipeline()
        self.normalization = NormalizationPipeline()

    def _valid_item(self):
        item = ListingItem()
        item["marketplace"] = "ebay"
        item["source_listing_id"] = "abc-123"
        item["url"] = "https://www.ebay.com/itm/abc-123"
        item["title"] = "  Chanel Bag  "
        item["price_amount"] = 2500.0
        item["currency"] = "usd"
        item["condition_raw"] = "Pre-owned"
        return item

    def test_validation_accepts_good_item(self):
        result = self.validation.process_item(self._valid_item(), self.spider)
        self.assertEqual(result["marketplace"], "ebay")

    def test_validation_drops_bad_price(self):
        item = self._valid_item()
        item["price_amount"] = 0
        with self.assertRaises(DropItem):
            self.validation.process_item(item, self.spider)

    def test_normalization_enriches_item(self):
        item = self.validation.process_item(self._valid_item(), self.spider)
        result = self.normalization.process_item(item, self.spider)
        self.assertEqual(result["title"], "Chanel Bag")
        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["condition_normalized"], "good")
        self.assertEqual(result["status"], "active")
        self.assertTrue(result["content_hash"])
        self.assertTrue(result["scraped_at"])


if __name__ == "__main__":
    unittest.main()
