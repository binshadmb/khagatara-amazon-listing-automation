import unittest
from types import SimpleNamespace

from src.products.discovery import discover_product_types


class ProductTypeDiscoveryTests(unittest.TestCase):
    def test_returns_normalised_amazon_candidates(self) -> None:
        client = SimpleNamespace(
            search_definitions_product_types=lambda **_: SimpleNamespace(
                payload={
                    "productTypes": [
                        {
                            "name": "SAREE",
                            "displayName": "Sarees",
                            "marketplaceIds": ["A21TJRUUN4KGV"],
                        },
                        {"productType": "APPAREL", "displayName": "Apparel"},
                    ]
                }
            )
        )

        result = discover_product_types(
            "  Kerala   Saree  ",
            marketplace_id="A21TJRUUN4KGV",
            client=client,
        )

        self.assertEqual(result.product_description, "  Kerala   Saree  ")
        self.assertEqual([item.product_type for item in result.candidates], ["SAREE", "APPAREL"])
        self.assertFalse(result.has_single_match)
        with self.assertRaisesRegex(ValueError, "Ask the user"):
            result.require_single_match()

    def test_requires_description(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            discover_product_types("   ", marketplace_id="A21TJRUUN4KGV", client=object())


if __name__ == "__main__":
    unittest.main()
