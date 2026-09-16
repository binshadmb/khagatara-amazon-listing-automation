"""Build Listings Items API payloads from locally validated product attributes."""

from typing import Any

from src.schemas.product_schema import ProductSchema
from src.validation.schema_validator import ValidationReport, validate_attributes


def build_listing_payload(
    *,
    sku: str,
    product_type: str,
    attributes: dict[str, Any],
    schema: ProductSchema,
    requirements: str = "LISTING",
) -> tuple[dict[str, Any], ValidationReport]:
    """Return a Listings Items API payload and its pre-submission validation report.

    The caller must not submit the payload when the accompanying report is invalid.
    """
    report = validate_attributes(attributes, schema)
    payload = {
        "sku": sku,
        "productType": product_type,
        "requirements": requirements,
        "attributes": attributes,
    }
    return payload, report
