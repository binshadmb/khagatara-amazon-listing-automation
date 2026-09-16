import unittest
from pathlib import Path

from src.products.variant_config import load_variant_option_catalog
from src.products.variants import VariantDimension, VariantOption, generate_variants


class VariantGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dimensions = [
            VariantDimension("fabric_type", (VariantOption("Cotton", "COT"), VariantOption("Tissue", "TIS"))),
            VariantDimension("body_colour", (VariantOption("White", "WHT"), VariantOption("Cream", "CRM"))),
            VariantDimension("border_width", (VariantOption("1 inch", "1"), VariantOption("2 inch", "2"))),
            VariantDimension("motif", (VariantOption("Peacock", "PEA"), VariantOption("Floral", "FLR"))),
        ]

    def test_generates_selected_combinations_and_skus(self) -> None:
        variants = generate_variants(base_sku="KS", base_attributes={"brand": "KHAGATARA"}, dimensions=self.dimensions)
        self.assertEqual(len(variants), 16)
        self.assertEqual(variants[0].sku, "KS-COT-WHT-1-PEA")
        self.assertEqual(variants[0].attributes["brand"], "KHAGATARA")

    def test_excludes_unavailable_combinations(self) -> None:
        variants = generate_variants(
            base_sku="KS",
            base_attributes={},
            dimensions=self.dimensions,
            excluded_combinations=[{"body_colour": "Cream", "motif": "Peacock"}],
        )
        self.assertEqual(len(variants), 12)
        self.assertFalse(any(item.attributes["body_colour"] == "Cream" and item.attributes["motif"] == "Peacock" for item in variants))

    def test_blocks_runaway_variant_counts(self) -> None:
        with self.assertRaisesRegex(ValueError, "would create 16 variants"):
            generate_variants(base_sku="KS", base_attributes={}, dimensions=self.dimensions, max_variants=10)

    def test_loads_expanded_option_catalog_without_generating_all_combinations(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "products" / "kerala_saree_variant_options.json"
        options = load_variant_option_catalog(path)
        self.assertGreaterEqual(len(options["body_colour"]), 20)
        self.assertIn("Custom", [option.value for option in options["motif"]])


if __name__ == "__main__":
    unittest.main()
