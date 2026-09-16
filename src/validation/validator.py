"""High-level validation of saved product JSON files against an Amazon schema."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.schemas.loader import load_schema
from src.schemas.parser import parse_amazon_definition
from src.schemas.product_schema import ProductSchema
from src.validation.schema_validator import ValidationReport, validate_attributes


@dataclass
class ProductFileValidationResult:
    product_file: Path
    sku: str | None
    product_type: str | None
    report: ValidationReport

    @property
    def is_valid(self) -> bool:
        return self.report.is_valid

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.is_valid,
            "product_file": str(self.product_file),
            "sku": self.sku,
            "product_type": self.product_type,
            "issues": [
                {"field": issue.field, "code": issue.code, "message": issue.message}
                for issue in self.report.issues
            ],
        }


def load_product_file(product_file: str | Path) -> dict[str, Any]:
    """Load and validate the outer structure of a product input JSON document."""
    path = Path(product_file)
    with path.open("r", encoding="utf-8") as file:
        product = json.load(file)
    if not isinstance(product, dict):
        raise ValueError("Product input must be a JSON object")
    if not isinstance(product.get("attributes"), dict):
        raise ValueError("Product input must contain an 'attributes' JSON object")
    return product


def validate_product_file(
    product_file: str | Path,
    schema: ProductSchema,
) -> ProductFileValidationResult:
    """Validate a product JSON file against an already parsed product schema."""
    path = Path(product_file)
    product = load_product_file(path)
    report = validate_attributes(product["attributes"], schema)
    return ProductFileValidationResult(
        product_file=path,
        sku=product.get("sku") if isinstance(product.get("sku"), str) else None,
        product_type=(
            product.get("product_type") if isinstance(product.get("product_type"), str) else None
        ),
        report=report,
    )


def validate_saved_product(
    product_file: str | Path,
    *,
    product_type: str,
    marketplace_id: str,
) -> ProductFileValidationResult:
    """Load a locally saved *resolved* Amazon schema and validate a product file."""
    raw_schema = load_schema(product_type, marketplace_id)
    schema = parse_amazon_definition(
        raw_schema,
        product_type=product_type,
        marketplace_id=marketplace_id,
    )
    return validate_product_file(product_file, schema)
