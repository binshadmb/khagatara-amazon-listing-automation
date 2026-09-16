"""Generic, configuration-driven product variant generation."""

from dataclasses import dataclass
from itertools import product
from typing import Any


@dataclass(frozen=True)
class VariantOption:
    value: str
    code: str


@dataclass(frozen=True)
class VariantDimension:
    attribute: str
    options: tuple[VariantOption, ...]


@dataclass(frozen=True)
class Variant:
    sku: str
    attributes: dict[str, Any]


def generate_variants(
    *,
    base_sku: str,
    base_attributes: dict[str, Any],
    dimensions: list[VariantDimension],
    excluded_combinations: list[dict[str, str]] | None = None,
    max_variants: int = 500,
) -> list[Variant]:
    """Create only selected variants, skipping explicit unavailable combinations.

    Each option carries an editable SKU code, so custom values never require a
    Python-code change. ``max_variants`` protects the local workflow from an
    accidental combinatorial explosion.
    """
    if not base_sku.strip():
        raise ValueError("base_sku cannot be empty")
    if max_variants < 1:
        raise ValueError("max_variants must be at least 1")
    if not dimensions:
        return [Variant(sku=base_sku, attributes=dict(base_attributes))]
    if any(not dimension.options for dimension in dimensions):
        raise ValueError("Every selected variant dimension needs at least one option")

    possible_count = 1
    for dimension in dimensions:
        possible_count *= len(dimension.options)
    if possible_count > max_variants:
        raise ValueError(
            f"Selected dimensions would create {possible_count} variants; "
            f"limit the selection or raise max_variants above {possible_count}."
        )

    exclusions = excluded_combinations or []
    variants: list[Variant] = []
    seen_skus: set[str] = set()
    for selected_options in product(*(dimension.options for dimension in dimensions)):
        values = {
            dimension.attribute: option.value
            for dimension, option in zip(dimensions, selected_options, strict=True)
        }
        if any(_matches_exclusion(values, exclusion) for exclusion in exclusions):
            continue

        sku = "-".join([base_sku, *(option.code.upper().strip() for option in selected_options)])
        if sku in seen_skus:
            raise ValueError(f"Duplicate SKU {sku!r}; give each selected option a unique code")
        seen_skus.add(sku)
        variants.append(Variant(sku=sku, attributes={**base_attributes, **values}))
    return variants


def _matches_exclusion(values: dict[str, str], exclusion: dict[str, str]) -> bool:
    return all(values.get(attribute) == value for attribute, value in exclusion.items())
