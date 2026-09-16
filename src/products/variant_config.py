"""Load editable variant plans from JSON without changing Python code."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.products.variants import VariantDimension, VariantOption


@dataclass(frozen=True)
class VariantPlan:
    base_sku: str
    base_attributes: dict[str, Any]
    dimensions: tuple[VariantDimension, ...]
    excluded_combinations: tuple[dict[str, str], ...]


def load_variant_plan(path: str | Path) -> VariantPlan:
    """Read a user-editable variant plan from JSON."""
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("Variant plan must be a JSON object")
    base_sku = data.get("base_sku")
    base_attributes = data.get("base_attributes", {})
    dimensions = data.get("dimensions", [])
    exclusions = data.get("excluded_combinations", [])
    if not isinstance(base_sku, str) or not base_sku:
        raise ValueError("Variant plan needs a base_sku")
    if not isinstance(base_attributes, dict) or not isinstance(dimensions, list) or not isinstance(exclusions, list):
        raise ValueError("Variant plan has invalid structure")

    return VariantPlan(
        base_sku=base_sku,
        base_attributes=base_attributes,
        dimensions=tuple(_parse_dimension(item) for item in dimensions),
        excluded_combinations=tuple(_parse_exclusion(item) for item in exclusions),
    )


def load_variant_option_catalog(path: str | Path) -> dict[str, tuple[VariantOption, ...]]:
    """Load reusable option libraries; a plan chooses only the options it sells."""
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)
    dimensions = data.get("dimensions") if isinstance(data, dict) else None
    if not isinstance(dimensions, dict):
        raise ValueError("Variant option catalog must contain a dimensions object")
    return {
        attribute: tuple(_parse_option(option) for option in options)
        for attribute, options in dimensions.items()
        if isinstance(attribute, str) and isinstance(options, list)
    }


def _parse_dimension(data: Any) -> VariantDimension:
    if not isinstance(data, dict) or not isinstance(data.get("attribute"), str):
        raise ValueError("Each dimension needs an attribute")
    options = data.get("options")
    if not isinstance(options, list):
        raise ValueError("Each dimension needs an options list")
    parsed = [_parse_option(option) for option in options]
    return VariantDimension(attribute=data["attribute"], options=tuple(parsed))


def _parse_option(option: Any) -> VariantOption:
    if not isinstance(option, dict) or not isinstance(option.get("value"), str) or not isinstance(option.get("code"), str):
        raise ValueError("Each option needs text value and code")
    return VariantOption(value=option["value"], code=option["code"])


def _parse_exclusion(data: Any) -> dict[str, str]:
    if not isinstance(data, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in data.items()):
        raise ValueError("Every exclusion must map attributes to text values")
    return data
