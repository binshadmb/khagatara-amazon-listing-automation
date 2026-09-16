import unittest

from src.products.attributes import load_attribute_catalog
from src.products.review import build_product_review


class ProductReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.category = load_attribute_catalog().category("kerala_saree")

    def test_combines_autofill_and_manual_data_into_review_report(self) -> None:
        review = build_product_review(
            {
                "description": "Cream Kerala cotton kasavu saree with golden peacock border for Onam",
                "attributes": {
                    "title": "Kasavu Saree",
                    "brand": "KHAGATARA",
                    "saree_length_cm": 630,
                    "width_cm": 120,
                    "blouse_piece_included": True,
                    "country_of_origin": "India",
                },
            },
            self.category,
        )
        report = review.to_dict()
        fields = {field["attribute"]: field for field in report["fields"]}
        self.assertEqual(fields["title"]["source"], "manual")
        self.assertEqual(fields["fabric_type"]["value"], "Kerala Cotton")
        self.assertIn("fabric_type", report["action_required"])
        self.assertEqual(report["local_issues"], [])

    def test_requires_manual_fields_when_no_source_is_available(self) -> None:
        review = build_product_review({"attributes": {}}, self.category)
        self.assertIn("title", review.action_required)
        self.assertFalse(review.is_ready_for_mapping)


if __name__ == "__main__":
    unittest.main()
