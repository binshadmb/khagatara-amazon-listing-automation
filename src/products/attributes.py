"""KHAGATARA's local category and attribute catalog."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "data" / "products" / "attribute_catalog.json"


@dataclass(frozen=True)
class AttributeDefinition:
    name: str
    label: str
    group: str
    data_type: str
    required: bool = False
    allowed_values: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProductCategory:
    key: str
    display_name: str
    attributes: tuple[AttributeDefinition, ...]

    def attribute(self, name: str) -> AttributeDefinition:
        for attribute in self.attributes:
            if attribute.name == name:
                return attribute
        raise KeyError(f"Unknown local attribute {name!r} for {self.display_name}")


@dataclass(frozen=True)
class AttributeCatalog:
    version: int
    categories: dict[str, ProductCategory]

    def category(self, key: str) -> ProductCategory:
        try:
            return self.categories[key]
        except KeyError as error:
            raise KeyError(f"Unknown product category {key!r}") from error


@dataclass(frozen=True)
class LocalAttributeIssue:
    attribute: str
    code: str
    message: str


def load_attribute_catalog(path: str | Path = DEFAULT_CATALOG_PATH) -> AttributeCatalog:
    """Load the versioned local attribute catalog from JSON."""
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict) or not isinstance(data.get("categories"), dict):
        raise ValueError("Attribute catalog must contain a categories object")

    categories: dict[str, ProductCategory] = {}
    for key, category_data in data["categories"].items():
        if not isinstance(category_data, dict) or not isinstance(category_data.get("attributes"), list):
            raise ValueError(f"Category {key!r} must contain an attributes list")
        attributes = tuple(_parse_attribute(item) for item in category_data["attributes"])
        categories[key] = ProductCategory(
            key=key,
            display_name=str(category_data.get("display_name", key)),
            attributes=attributes,
        )
    return AttributeCatalog(version=int(data.get("version", 1)), categories=categories)


def validate_local_attributes(
    attributes: dict[str, Any],
    category: ProductCategory,
) -> list[LocalAttributeIssue]:
    """Check local required fields and catalog-controlled allowed values."""
    issues: list[LocalAttributeIssue] = []
    definitions = {attribute.name: attribute for attribute in category.attributes}

    for name, definition in definitions.items():
        value = attributes.get(name)
        if definition.required and (value is None or value == "" or value == []):
            issues.append(LocalAttributeIssue(name, "REQUIRED", "A local value is required."))
        if value is not None and not _matches_type(value, definition.data_type):
            issues.append(
                LocalAttributeIssue(
                    name,
                    "TYPE",
                    f"Expected {definition.data_type} data.",
                )
            )
        if value is not None and definition.allowed_values and value not in definition.allowed_values:
            issues.append(
                LocalAttributeIssue(
                    name,
                    "ALLOWED_VALUES",
                    f"Use one of: {', '.join(definition.allowed_values)}.",
                )
            )

    for name in attributes:
        if name not in definitions:
            issues.append(LocalAttributeIssue(name, "UNKNOWN_ATTRIBUTE", "Not in this local category."))
    return issues


def _matches_type(value: Any, data_type: str) -> bool:
    if data_type in {"text", "enum"}:
        return isinstance(value, str)
    if data_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if data_type == "boolean":
        return isinstance(value, bool)
    return True


def _parse_attribute(data: Any) -> AttributeDefinition:
    if not isinstance(data, dict):
        raise ValueError("Each attribute definition must be an object")
    name = data.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("Each attribute definition needs a name")
    allowed_values = data.get("allowed_values", [])
    if not isinstance(allowed_values, list) or not all(isinstance(value, str) for value in allowed_values):
        raise ValueError(f"Attribute {name!r} has invalid allowed_values")
    return AttributeDefinition(
        name=name,
        label=str(data.get("label", name.replace("_", " ").title())),
        group=str(data.get("group", "General")),
        data_type=str(data.get("data_type", "text")),
        required=bool(data.get("required", False)),
        allowed_values=tuple(allowed_values),
    )
