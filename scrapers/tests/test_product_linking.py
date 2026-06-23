import unittest

from bags.product_linking import is_likely_accessory, should_link_listing
from bags.title_parser import ParsedProduct, parse_title


class ProductLinkingTest(unittest.TestCase):
    def test_accessory_charm(self):
        title = "Hermes Birkin Bag Charm New"
        self.assertTrue(is_likely_accessory(title))
        self.assertFalse(should_link_listing(title, 4000.0))

    def test_accessory_silicone_cover(self):
        title = "Clear Silicone Protective cover for handbag stud feet for hermes Birkin 25, 30"
        self.assertTrue(is_likely_accessory(title))
        self.assertFalse(should_link_listing(title, 29.99))

    def test_accessory_gift_box(self):
        title = "HERMES Birkin 30 empty Gift Box 36×38×15.5cm"
        self.assertTrue(is_likely_accessory(title))
        self.assertFalse(should_link_listing(title, 382.0))

    def test_birkin_under_5000_not_linked(self):
        title = "Hermes Birkin 35 Taurillon Clemence White Hand Bag"
        parsed = parse_title(title)
        self.assertFalse(should_link_listing(title, 4000.0, parsed))

    def test_birkin_at_5000_linked(self):
        title = "Hermes Birkin 30 Togo Gold"
        parsed = parse_title(title)
        self.assertTrue(should_link_listing(title, 5000.0, parsed))

    def test_birkin_without_variant_not_linked(self):
        title = "Hermes Birkin authentic handbag"
        parsed = parse_title(title)
        self.assertIsNotNone(parsed)
        self.assertFalse(should_link_listing(title, 8000.0, parsed))

    def test_real_birkin_linked(self):
        title = "Hermes Birkin 30 Authentic Etoupe/Beige"
        parsed = parse_title(title)
        self.assertTrue(should_link_listing(title, 14600.0, parsed))

    def test_hac_not_subject_to_birkin_floor(self):
        title = "Authentic HERMES Haut à Courroies 32 HAC Birkin red Box leather vintage 1995"
        parsed = parse_title(title)
        self.assertEqual(parsed.model, "Haut à Courroies")
        self.assertTrue(should_link_listing(title, 7999.0, parsed))


if __name__ == "__main__":
    unittest.main()
