import unittest

from bags.title_parser import parse_title


class TitleParserTest(unittest.TestCase):
    def test_hermes_birkin_full_title(self):
        parsed = parse_title("Hermès Togo Birkin 30 Gold")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.brand, "Hermès")
        self.assertEqual(parsed.model, "Birkin")
        self.assertEqual(parsed.size, "30")
        self.assertEqual(parsed.leather, "Togo")
        self.assertEqual(parsed.color, "Gold")

    def test_chanel_classic_flap(self):
        parsed = parse_title("Chanel Lambskin Quilted Classic Double Flap Bag")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.brand, "Chanel")
        self.assertEqual(parsed.model, "Classic Double Flap")
        self.assertEqual(parsed.leather, "Lambskin")

    def test_ebay_birkin_title(self):
        parsed = parse_title("Hermes Birkin 30 Authentic Etoupe/Beige")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.brand, "Hermès")
        self.assertEqual(parsed.model, "Birkin")
        self.assertEqual(parsed.size, "30")
        self.assertEqual(parsed.color, "Etoupe")

    def test_hac_title(self):
        parsed = parse_title("Authentic HERMES Birkin HAC Haut à Courroies 32 brown courchevel leather bag")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Haut à Courroies")
        self.assertEqual(parsed.size, "32")
        self.assertEqual(parsed.leather, "Courchevel")
        self.assertEqual(parsed.color, "Brown")

    def test_accessory_without_model_returns_none(self):
        parsed = parse_title("Clear Silicone Protective cover for handbag stud feet")
        self.assertIsNone(parsed)

    def test_gift_box_does_not_match_box_leather(self):
        parsed = parse_title("HERMES Birkin 30 empty Gift Box 36×38×15.5cm")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Birkin")
        self.assertIsNone(parsed.leather)

    def test_hardware_not_parsed_as_color(self):
        parsed = parse_title(
            "Hermes Birkin 30 Tanzanite BlueTogo Leather Bag Gold Tone D Stamp 2019"
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.color, "Tanzanite Blue")
        self.assertEqual(parsed.leather, "Togo")


if __name__ == "__main__":
    unittest.main()
