"""Local validation for the subset of Amazon JSON Schema used by listing attributes."""

from dataclasses import dataclass, field
from typing import Any

from src.schemas.product_schema import ProductSchema


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    code: str
    message: str


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues


def validate_attributes(
    attributes: dict[str, Any],
    schema: ProductSchema,
) -> ValidationReport:
    """Validate required fields and common Amazon array/value constraints locally."""
    report = ValidationReport()

    for field in schema.fields:
        value = attributes.get(field.name)
        if field.required and (value is None or value == [] or value == ""):
            report.issues.append(
                ValidationIssue(field.name, "REQUIRED", "A value is required for this field.")
            )
            continue
        if value is None:
            continue

        constraints = field.constraints
        expected_type = constraints.get("type")
        if expected_type == "array":
            if not isinstance(value, list):
                report.issues.append(
                    ValidationIssue(field.name, "TYPE", "Expected an array of attribute values.")
                )
                continue
            _validate_array_bounds(field.name, value, constraints, report)
            _validate_items(field.name, value, constraints.get("items"), report)
        elif expected_type == "string" and not isinstance(value, str):
            report.issues.append(ValidationIssue(field.name, "TYPE", "Expected text."))

    return report


def _validate_array_bounds(
    name: str,
    value: list[Any],
    constraints: dict[str, Any],
    report: ValidationReport,
) -> None:
    minimum = constraints.get("minItems")
    maximum = constraints.get("maxItems")
    if isinstance(minimum, int) and len(value) < minimum:
        report.issues.append(ValidationIssue(name, "MIN_ITEMS", f"At least {minimum} value(s) required."))
    if isinstance(maximum, int) and len(value) > maximum:
        report.issues.append(ValidationIssue(name, "MAX_ITEMS", f"At most {maximum} value(s) allowed."))


def _validate_items(
    name: str,
    values: list[Any],
    item_schema: Any,
    report: ValidationReport,
) -> None:
    if not isinstance(item_schema, dict):
        return
    for index, item in enumerate(values):
        if item_schema.get("type") == "object" and not isinstance(item, dict):
            report.issues.append(ValidationIssue(name, "ITEM_TYPE", f"Item {index} must be an object."))
            continue
        properties = item_schema.get("properties", {})
        if not isinstance(item, dict) or not isinstance(properties, dict):
            continue
        value_constraint = properties.get("value")
        item_value = item.get("value")
        if isinstance(value_constraint, dict) and value_constraint.get("type") == "string":
            if not isinstance(item_value, str):
                report.issues.append(ValidationIssue(name, "VALUE_TYPE", f"Item {index} value must be text."))
                continue
            minimum = value_constraint.get("minLength")
            maximum = value_constraint.get("maxLength")
            if isinstance(minimum, int) and len(item_value) < minimum:
                report.issues.append(ValidationIssue(name, "MIN_LENGTH", f"Item {index} is too short."))
            if isinstance(maximum, int) and len(item_value) > maximum:
                report.issues.append(ValidationIssue(name, "MAX_LENGTH", f"Item {index} is too long."))
