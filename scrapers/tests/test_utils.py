import unittest

from bags.utils import compute_content_hash, normalize_condition


class UtilsTest(unittest.TestCase):
    def test_normalize_condition(self):
        self.assertEqual(normalize_condition("Very Good"), "very_good")
        self.assertEqual(normalize_condition("Pre-owned"), "good")

    def test_content_hash_stable(self):
        fields = {"title": "Birkin", "brand": "Hermès", "model": "Birkin"}
        h1 = compute_content_hash(fields)
        h2 = compute_content_hash(fields)
        self.assertEqual(h1, h2)


if __name__ == "__main__":
    unittest.main()
