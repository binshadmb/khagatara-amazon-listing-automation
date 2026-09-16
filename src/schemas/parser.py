"""Convert Amazon Product Type Definition payloads to the app's field model."""

from typing import Any

from src.schemas.product_schema import ProductField, ProductSchema


def parse_amazon_definition(
    definition: dict[str, Any],
    *,
    product_type: str | None = None,
    marketplace_id: str,
) -> ProductSchema:
    """Build a ``ProductSchema`` from an SP-API Product Type Definition payload.

    Amazon places listing attributes in ``schema.properties`` and marks required
    attributes in ``schema.required``. The original JSON-schema fragment is kept
    as each field's constraints so validation can be extended without refetching.
    """
    schema = definition.get("schema", definition)
    if not isinstance(schema, dict):
        raise ValueError("Amazon definition does not contain a JSON-schema object")
    if "link" in schema and "properties" not in schema:
        raise RuntimeError(
            "This Product Type Definition contains a schema download link, not the "
            "schema itself. Download the linked schema before parsing or validating."
        )

    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise ValueError("Amazon definition schema has invalid properties")

    required = schema.get("required", [])
    if not isinstance(required, list):
        required = []
    required_names = set(required)

    fields = [
        ProductField(
            name=name,
            required=name in required_names,
            constraints=constraints if isinstance(constraints, dict) else {},
        )
        for name, constraints in properties.items()
    ]

    return ProductSchema(
        product_type=product_type or str(definition.get("productType", "UNKNOWN")),
        marketplace_id=marketplace_id,
        fields=fields,
    )
