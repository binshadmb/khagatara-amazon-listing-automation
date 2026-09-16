import unittest

from src.ai.confidence import EvidenceSource, FieldSuggestion
from src.products.attributes import load_attribute_catalog
from src.products.autofill import autofill_product


class AutofillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.category = load_attribute_catalog().category("kerala_saree")

    def test_extracts_reviewable_text_suggestions(self) -> None:
        result = autofill_product(
            category=self.category,
            description="Kerala cotton kasavu saree with golden peacock border for Onam",
        )
        attributes = result.attributes()
        self.assertEqual(attributes["fabric_type"], "Kerala Cotton")
        self.assertEqual(attributes["border_colour"], "Gold")
        self.assertEqual(attributes["motif"], "Peacock")
        self.assertIn("title", result.manual_fields)

    def test_prefers_higher_confidence_and_flags_conflicts(self) -> None:
        result = autofill_product(
            category=self.category,
            suggestions=[
                FieldSuggestion("body_colour", "Cream", 0.80, EvidenceSource.DESCRIPTION, "cream"),
                FieldSuggestion("body_colour", "White", 0.95, EvidenceSource.SUPPLIER_CATALOG, "supplier SKU"),
            ],
        )
        field = result.fields["body_colour"]
        self.assertEqual(field.suggestion.value, "White")
        self.assertEqual(field.review_state, "conflicting")


if __name__ == "__main__":
    unittest.main()
