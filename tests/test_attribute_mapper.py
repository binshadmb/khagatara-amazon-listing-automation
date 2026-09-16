import unittest

from src.schemas.mapper import AttributeMapping, map_attributes
from src.schemas.parser import parse_amazon_definition


class AttributeMapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = parse_amazon_definition(
            {
                "schema": {
                    "required": ["item_name", "material"],
                    "properties": {
                        "item_name": {"type": "array", "minItems": 1},
                        "material": {"type": "array", "minItems": 1},
                        "is_adult_product": {"type": "array"},
                    },
                }
            },
            product_type="SAREE",
            marketplace_id="A21TJRUUN4KGV",
        )

    def test_maps_local_attributes_to_amazon_value_arrays(self) -> None:
        result = map_attributes(
            {"title": "Kasavu Saree", "fabric_type": "Kerala Cotton", "adult": False},
            [
                AttributeMapping("title", "item_name"),
                AttributeMapping("fabric_type", "material"),
                AttributeMapping("adult", "is_adult_product", "yes_no"),
            ],
            self.schema,
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.attributes["item_name"], [{"value": "Kasavu Saree"}])
        self.assertEqual(result.attributes["is_adult_product"], [{"value": "No"}])

    def test_reports_unknown_target_and_missing_required_mapping(self) -> None:
        result = map_attributes(
            {"title": "Kasavu Saree"},
            [
                AttributeMapping("title", "item_name"),
                AttributeMapping("border_type", "kasavu_border"),
            ],
            self.schema,
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.issues[0].code, "UNKNOWN_AMAZON_ATTRIBUTE")
        self.assertEqual(result.validation.issues[0].field, "material")


if __name__ == "__main__":
    unittest.main()
