import unittest

from src.ai.text_analyzer import analyze_text
from src.products.attributes import load_attribute_catalog
from src.products.category_detection import detect_categories


class SupportedCategoryTests(unittest.TestCase):
    def test_catalog_contains_requested_categories(self) -> None:
        catalog = load_attribute_catalog()
        self.assertEqual(catalog.category("saree").display_name, "Saree")
        self.assertEqual(catalog.category("women_kurti").display_name, "Women’s Kurti")
        self.assertEqual(catalog.category("women_top").display_name, "Women’s Top")

    def test_detects_requested_categories(self) -> None:
        self.assertEqual(detect_categories("Kasavu Kerala saree")[0].category, "kerala_saree")
        self.assertEqual(detect_categories("Floral silk sari")[0].category, "saree")
        self.assertEqual(detect_categories("Long cotton kurti")[0].category, "women_kurti")
        self.assertEqual(detect_categories("Ladies top short sleeve")[0].category, "women_top")

    def test_extracts_kurti_length_and_sleeve(self) -> None:
        values = {item.attribute: item.value for item in analyze_text("Long cotton kurti with three quarter sleeves", category="women_kurti")}
        self.assertEqual(values["fabric_type"], "Cotton")
        self.assertEqual(values["garment_length"], "Long")
        self.assertEqual(values["sleeve_length"], "Three Quarter Sleeve")


if __name__ == "__main__":
    unittest.main()
