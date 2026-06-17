import unittest

from bags.items import ListingItem
from bags.spiders.dev_sample import DevSampleSpider


class DevSampleSpiderTest(unittest.TestCase):
    def setUp(self):
        self.spider = DevSampleSpider()

    def test_sample_rows_count(self):
        self.assertEqual(len(list(self.spider._sample_rows())), 2)

    async def _collect_items(self):
        items = []
        async for result in self.spider.start():
            if isinstance(result, ListingItem):
                items.append(result)
        return items

    def test_start_yields_two_items(self):
        import asyncio

        items = asyncio.run(self._collect_items())
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["marketplace"], "ebay")
        self.assertEqual(items[1]["marketplace"], "therealreal")
        self.assertEqual(items[0]["price_amount"], 6500.0)


if __name__ == "__main__":
    unittest.main()
