import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.schemas.mapping_profiles import load_mapping_profile, map_with_profile
from src.schemas.parser import parse_amazon_definition


class MappingProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = parse_amazon_definition(
            {"schema": {"properties": {"item_name": {"type": "array"}}}},
            product_type="SAREE",
            marketplace_id="A21TJRUUN4KGV",
        )

    def test_draft_profile_cannot_create_amazon_payload(self) -> None:
        profile = self._profile("draft", "SAREE")
        with self.assertRaisesRegex(ValueError, "approved"):
            map_with_profile({"title": "Kasavu Saree"}, profile, self.schema)

    def test_approved_matching_profile_maps_attributes(self) -> None:
        profile = self._profile("approved", "SAREE")
        result = map_with_profile({"title": "Kasavu Saree"}, profile, self.schema)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.attributes["item_name"], [{"value": "Kasavu Saree"}])

    def test_profile_must_match_selected_schema_product_type(self) -> None:
        profile = self._profile("approved", "APPAREL")
        with self.assertRaisesRegex(ValueError, "does not match"):
            map_with_profile({}, profile, self.schema)

    def _profile(self, status: str, product_type: str):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text(json.dumps({
                "version": 1,
                "local_category": "kerala_saree",
                "amazon_product_type": product_type,
                "status": status,
                "mappings": [{"local_attribute": "title", "amazon_attribute": "item_name"}],
            }), encoding="utf-8")
            return load_mapping_profile(path)


if __name__ == "__main__":
    unittest.main()
