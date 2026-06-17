import unittest

from bags.utils import compute_content_hash, normalize_condition


class UtilsTest(unittest.TestCase):
    def test_normalize_condition(self):
        self.assertEqual(normalize_condition("Very Good"), "very_good")
        self.assertEqual(normalize_condition("Pre-owned"), "good")

    def test_content_hash_stable(self):
        fields = {"title": "Birkin", "price_amount": 1000, "currency": "USD"}
        self.assertEqual(compute_content_hash(fields), compute_content_hash(fields))


if __name__ == "__main__":
    unittest.main()
