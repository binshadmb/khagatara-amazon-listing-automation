"""Map KHAGATARA local attributes to attributes accepted by an Amazon schema."""

from dataclasses import dataclass, field
from typing import Any, Literal

from src.schemas.product_schema import ProductSchema
from src.validation.schema_validator import ValidationReport, validate_attributes

Transform = Literal["identity", "value_array", "yes_no"]


@dataclass(frozen=True)
class AttributeMapping:
    local_attribute: str
    amazon_attribute: str
    transform: Transform = "value_array"


@dataclass(frozen=True)
class MappingIssue:
    local_attribute: str
    code: str
    message: str


@dataclass
class MappingResult:
    attributes: dict[str, Any] = field(default_factory=dict)
    issues: list[MappingIssue] = field(default_factory=list)
    validation: ValidationReport | None = None

    @property
    def is_valid(self) -> bool:
        return not self.issues and (self.validation is None or self.validation.is_valid)


def map_attributes(
    local_attributes: dict[str, Any],
    mappings: list[AttributeMapping],
    amazon_schema: ProductSchema,
) -> MappingResult:
    """Map explicit local values to Amazon attributes and validate the result."""
    result = MappingResult()
    amazon_fields = set(amazon_schema.field_names())
    for mapping in mappings:
        if mapping.amazon_attribute not in amazon_fields:
            result.issues.append(
                MappingIssue(
                    mapping.local_attribute,
                    "UNKNOWN_AMAZON_ATTRIBUTE",
                    f"{mapping.amazon_attribute!r} is not available in the selected Amazon schema.",
                )
            )
            continue
        if mapping.local_attribute not in local_attributes:
            continue
        try:
            result.attributes[mapping.amazon_attribute] = _transform(
                local_attributes[mapping.local_attribute], mapping.transform
            )
        except ValueError as error:
            result.issues.append(MappingIssue(mapping.local_attribute, "TRANSFORM", str(error)))
    result.validation = validate_attributes(result.attributes, amazon_schema)
    return result


def _transform(value: Any, transform: Transform) -> Any:
    if transform == "identity":
        return value
    if transform == "value_array":
        return [{"value": item} for item in value] if isinstance(value, list) else [{"value": value}]
    if transform == "yes_no":
        if not isinstance(value, bool):
            raise ValueError("yes_no transform requires a boolean local value")
        return [{"value": "Yes" if value else "No"}]
    raise ValueError(f"Unsupported transform {transform!r}")
