import unittest

from src.products.attributes import load_attribute_catalog, validate_local_attributes


class AttributeCatalogTests(unittest.TestCase):
    def test_loads_kerala_saree_catalog(self) -> None:
        catalog = load_attribute_catalog()
        saree = catalog.category("kerala_saree")

        self.assertGreaterEqual(len(saree.attributes), 20)
        self.assertEqual(saree.attribute("fabric_type").group, "Material & Construction")

    def test_validates_required_and_allowed_values(self) -> None:
        saree = load_attribute_catalog().category("kerala_saree")
        issues = validate_local_attributes(
            {"fabric_type": "Denim", "saree_length_cm": "six", "unknown": "value"},
            saree,
        )

        codes = {(issue.attribute, issue.code) for issue in issues}
        self.assertIn(("title", "REQUIRED"), codes)
        self.assertIn(("fabric_type", "ALLOWED_VALUES"), codes)
        self.assertIn(("saree_length_cm", "TYPE"), codes)
        self.assertIn(("unknown", "UNKNOWN_ATTRIBUTE"), codes)


if __name__ == "__main__":
    unittest.main()
