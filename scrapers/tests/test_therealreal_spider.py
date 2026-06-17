import unittest

from scrapy.http import HtmlResponse

from bags.items import ListingItem
from bags.spiders.therealreal import TherealrealSpider


class TherealrealSpiderTest(unittest.TestCase):
    def setUp(self):
        self.spider = TherealrealSpider()

    def test_parse_price(self):
        self.assertEqual(self.spider._parse_price("$4,850.00"), 4850.0)
        self.assertIsNone(self.spider._parse_price(""))

    def test_build_item(self):
        item = self.spider._build_item(
            "https://www.therealreal.com/products/chanel-bag-123",
            "Chanel Classic Flap",
            "$3,200",
            "https://www.therealreal.com/designers/chanel/women/handbags",
        )
        self.assertIsInstance(item, ListingItem)
        self.assertEqual(item["marketplace"], "therealreal")
        self.assertEqual(item["price_amount"], 3200.0)

    def test_parse_product_card(self):
        html = """
        <html><body>
          <a href="/products/chanel-flap-123">
            <div data-testid="product-title">Chanel Classic Flap</div>
            <div data-testid="product-price">$3,100.00</div>
          </a>
        </body></html>
        """
        response = HtmlResponse(
            url="https://www.therealreal.com/designers/chanel/women/handbags",
            body=html.encode(),
            encoding="utf-8",
        )
        items = [r for r in self.spider.parse(response) if isinstance(r, ListingItem)]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Chanel Classic Flap")

    def test_mock_items(self):
        items = list(self.spider._mock_items())
        self.assertEqual(len(items), 2)


if __name__ == "__main__":
    unittest.main()
