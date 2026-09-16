import unittest

from src.products.approval import apply_approvals
from src.products.attributes import load_attribute_catalog
from src.products.review import build_product_review


class ApprovalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.category = load_attribute_catalog().category("women_kurti")
        self.review = build_product_review(
            {
                "description": "Long cotton kurti with three quarter sleeves and floral print",
                "attributes": {"title": "Floral Kurti", "brand": "KHAGATARA", "size": "M", "country_of_origin": "India"},
            },
            self.category,
        )

    def test_accepts_and_edits_all_unresolved_fields(self) -> None:
        confirmed = apply_approvals(
            self.review,
            self.category,
            {"accept": ["fabric_type", "pattern", "sleeve_length"], "edits": {"colour": "Blue", "garment_length": "Long"}},
        )
        self.assertTrue(confirmed.ready_for_mapping)
        self.assertEqual(confirmed.approvals["colour"], "edited")
        self.assertEqual(confirmed.attributes["garment_length"], "Long")

    def test_unaccepted_suggestions_remain_blocked(self) -> None:
        confirmed = apply_approvals(self.review, self.category, {"accept": [], "edits": {}})
        self.assertFalse(confirmed.ready_for_mapping)
        self.assertIn("fabric_type", confirmed.action_required)


if __name__ == "__main__":
    unittest.main()
