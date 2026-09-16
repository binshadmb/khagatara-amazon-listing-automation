import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import httpx

from src.amazon.product_types import get_definition_with_retry
from src.products.listing_payload import build_listing_payload
from src.schemas import loader
from src.schemas.parser import parse_amazon_definition
from src.schemas.resolver import schema_url_from_definition
from src.validation.schema_validator import validate_attributes
from src.validation.validator import validate_product_file


class ProductDefinitionFlowTests(unittest.TestCase):
    def test_retries_timeout_then_returns_definition(self) -> None:
        client = Mock()
        expected = Mock(payload={"productType": "LUGGAGE"})
        client.get_definitions_product_type.side_effect = [
            httpx.ConnectTimeout("temporary timeout"),
            expected,
        ]

        result = get_definition_with_retry(
            client,
            product_type="LUGGAGE",
            marketplace_id="A21TJRUUN4KGV",
            initial_backoff_seconds=0,
            sleep=lambda _: None,
        )

        self.assertIs(result, expected)
        self.assertEqual(client.get_definitions_product_type.call_count, 2)

    def test_parser_preserves_required_fields_and_constraints(self) -> None:
        definition = {
            "productType": "LUGGAGE",
            "schema": {
                "required": ["item_name", "brand"],
                "properties": {
                    "item_name": {"type": "array", "minItems": 1},
                    "brand": {"type": "array"},
                    "color": {"type": "array"},
                },
            },
        }

        parsed = parse_amazon_definition(
            definition,
            marketplace_id="A21TJRUUN4KGV",
        )

        self.assertEqual(parsed.product_type, "LUGGAGE")
        self.assertEqual([field.name for field in parsed.required_fields()], ["item_name", "brand"])
        self.assertEqual(parsed.fields[0].constraints["minItems"], 1)

    def test_loader_uses_project_path_not_current_directory(self) -> None:
        original_directory = loader.SCHEMA_DIR
        with TemporaryDirectory() as temporary_directory:
            loader.SCHEMA_DIR = Path(temporary_directory)
            try:
                path = loader.save_schema("LUGGAGE", "A21TJRUUN4KGV", {"ok": True})
                self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"ok": True})
                self.assertEqual(loader.load_schema("LUGGAGE", "A21TJRUUN4KGV"), {"ok": True})
            finally:
                loader.SCHEMA_DIR = original_directory

    def test_schema_url_rejects_sandbox_placeholder(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "placeholder"):
            schema_url_from_definition(
                {"schema": {"link": {"resource": "https://schema-url", "verb": "GET"}}}
            )

    def test_validates_and_builds_a_listing_payload(self) -> None:
        schema = parse_amazon_definition(
            {
                "productType": "LUGGAGE",
                "schema": {
                    "required": ["item_name"],
                    "properties": {
                        "item_name": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "type": "object",
                                "properties": {"value": {"type": "string", "minLength": 3}},
                            },
                        }
                    },
                },
            },
            marketplace_id="A21TJRUUN4KGV",
        )
        invalid = validate_attributes({}, schema)
        self.assertFalse(invalid.is_valid)
        self.assertEqual(invalid.issues[0].code, "REQUIRED")

        attributes = {"item_name": [{"value": "Travel bag"}]}
        payload, report = build_listing_payload(
            sku="BAG-001",
            product_type="LUGGAGE",
            attributes=attributes,
            schema=schema,
        )
        self.assertTrue(report.is_valid)
        self.assertEqual(payload["attributes"], attributes)

    def test_validates_product_json_file_and_formats_report(self) -> None:
        schema = parse_amazon_definition(
            {
                "schema": {
                    "required": ["brand"],
                    "properties": {"brand": {"type": "array", "minItems": 1}},
                }
            },
            product_type="LUGGAGE",
            marketplace_id="A21TJRUUN4KGV",
        )
        with TemporaryDirectory() as temporary_directory:
            product_file = Path(temporary_directory) / "my-saree.json"
            product_file.write_text(
                json.dumps({"sku": "SAREE-001", "product_type": "LUGGAGE", "attributes": {}}),
                encoding="utf-8",
            )
            result = validate_product_file(product_file, schema)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.to_dict()["issues"][0]["field"], "brand")


if __name__ == "__main__":
    unittest.main()
