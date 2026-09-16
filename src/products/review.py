"""Integrated, human-reviewable local product draft workflow."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ai.confidence import EvidenceSource, FieldSuggestion
from src.products.attributes import LocalAttributeIssue, ProductCategory, validate_local_attributes
from src.products.autofill import AutofillField, autofill_product


@dataclass(frozen=True)
class ReviewField:
    attribute: str
    value: Any
    source: str
    confidence: float | None
    review_state: str


@dataclass(frozen=True)
class ProductReview:
    category: str
    fields: tuple[ReviewField, ...]
    local_issues: tuple[LocalAttributeIssue, ...]
    action_required: tuple[str, ...]

    @property
    def is_ready_for_mapping(self) -> bool:
        return not self.local_issues and not self.action_required

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "ready_for_mapping": self.is_ready_for_mapping,
            "fields": [
                {
                    "attribute": item.attribute,
                    "value": item.value,
                    "source": item.source,
                    "confidence": item.confidence,
                    "review_state": item.review_state,
                }
                for item in self.fields
            ],
            "local_issues": [
                {"attribute": issue.attribute, "code": issue.code, "message": issue.message}
                for issue in self.local_issues
            ],
            "action_required": list(self.action_required),
        }


def build_product_review(
    product_draft: dict[str, Any],
    category: ProductCategory,
) -> ProductReview:
    """Combine auto-fill and manual input into one reviewable local draft."""
    description = product_draft.get("description", "")
    filename = product_draft.get("filename", "")
    manual_attributes = product_draft.get("attributes", {})
    if not isinstance(description, str) or not isinstance(filename, str):
        raise ValueError("description and filename must be text")
    if not isinstance(manual_attributes, dict):
        raise ValueError("attributes must be an object")

    auto = autofill_product(category=category, description=description, filename=filename)
    combined = auto.attributes()
    combined.update(manual_attributes)
    local_issues = tuple(validate_local_attributes(combined, category))

    fields: list[ReviewField] = []
    action_required: set[str] = set(auto.manual_fields)
    for definition in category.attributes:
        if definition.name in manual_attributes:
            fields.append(
                ReviewField(
                    attribute=definition.name,
                    value=manual_attributes[definition.name],
                    source=EvidenceSource.MANUAL.value,
                    confidence=1.0,
                    review_state="manual",
                )
            )
            action_required.discard(definition.name)
            continue
        auto_field = auto.fields.get(definition.name)
        if auto_field is not None:
            fields.append(_review_field(definition.name, auto_field))
            if auto_field.review_state in {"medium", "needs_confirmation", "conflicting"}:
                action_required.add(definition.name)
            continue
        if definition.required:
            fields.append(ReviewField(definition.name, None, "none", None, "required"))

    action_required.update(issue.attribute for issue in local_issues)
    return ProductReview(
        category=category.key,
        fields=tuple(fields),
        local_issues=local_issues,
        action_required=tuple(sorted(action_required)),
    )


def load_product_draft(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("Product draft must be a JSON object")
    return data


def _review_field(attribute: str, field: AutofillField) -> ReviewField:
    return ReviewField(
        attribute=attribute,
        value=field.suggestion.value,
        source=field.suggestion.source.value,
        confidence=field.suggestion.confidence,
        review_state=field.review_state,
    )
