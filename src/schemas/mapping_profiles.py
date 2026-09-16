"""Versioned mapping profiles between local categories and Amazon product types."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.schemas.mapper import AttributeMapping, MappingResult, map_attributes
from src.schemas.product_schema import ProductSchema


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE_DIR = PROJECT_ROOT / "data" / "mappings"


@dataclass(frozen=True)
class MappingProfile:
    version: int
    local_category: str
    amazon_product_type: str
    status: str
    mappings: tuple[AttributeMapping, ...]

    @property
    def is_approved(self) -> bool:
        return self.status == "approved"


def load_mapping_profile(path: str | Path) -> MappingProfile:
    """Load one explicit, versioned local-to-Amazon mapping profile."""
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("Mapping profile must be a JSON object")

    status = data.get("status")
    if status not in {"draft", "approved", "retired"}:
        raise ValueError("Mapping profile status must be draft, approved, or retired")
    mappings = data.get("mappings")
    if not isinstance(mappings, list):
        raise ValueError("Mapping profile must contain a mappings list")

    return MappingProfile(
        version=int(data.get("version", 1)),
        local_category=_required_text(data, "local_category"),
        amazon_product_type=_required_text(data, "amazon_product_type"),
        status=status,
        mappings=tuple(_parse_mapping(item) for item in mappings),
    )


def map_with_profile(
    local_attributes: dict[str, Any],
    profile: MappingProfile,
    amazon_schema: ProductSchema,
) -> MappingResult:
    """Map attributes only when an approved profile matches the selected schema."""
    if not profile.is_approved:
        raise ValueError("Only an approved mapping profile may be used for an Amazon payload")
    if profile.amazon_product_type != amazon_schema.product_type:
        raise ValueError(
            "Mapping profile product type does not match the selected Amazon schema"
        )
    return map_attributes(local_attributes, list(profile.mappings), amazon_schema)


def _required_text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Mapping profile needs a non-empty {key!r}")
    return value


def _parse_mapping(data: Any) -> AttributeMapping:
    if not isinstance(data, dict):
        raise ValueError("Every mapping must be an object")
    local_attribute = _required_text(data, "local_attribute")
    amazon_attribute = _required_text(data, "amazon_attribute")
    transform = data.get("transform", "value_array")
    if transform not in {"identity", "value_array", "yes_no"}:
        raise ValueError(f"Unsupported mapping transform {transform!r}")
    return AttributeMapping(local_attribute, amazon_attribute, transform)
