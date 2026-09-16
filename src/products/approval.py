"""Apply human approvals and edits to a product review before Amazon mapping."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.products.attributes import ProductCategory, validate_local_attributes
from src.products.review import ProductReview


@dataclass(frozen=True)
class ConfirmedProductDraft:
    category: str
    attributes: dict[str, Any]
    approvals: dict[str, str]
    action_required: tuple[str, ...]
    local_issues: tuple[dict[str, str], ...]

    @property
    def ready_for_mapping(self) -> bool:
        return not self.action_required and not self.local_issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "ready_for_mapping": self.ready_for_mapping,
            "attributes": self.attributes,
            "approvals": self.approvals,
            "action_required": list(self.action_required),
            "local_issues": list(self.local_issues),
        }


def load_approval_file(path: str | Path) -> dict[str, Any]:
    """Load a simple approval file: accept fields and optionally provide edits."""
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("Approval file must be a JSON object")
    if not isinstance(data.get("accept", []), list) or not isinstance(data.get("edits", {}), dict):
        raise ValueError("Approval file requires an accept list and edits object")
    return data


def apply_approvals(
    review: ProductReview,
    category: ProductCategory,
    approval: dict[str, Any],
) -> ConfirmedProductDraft:
    """Accept extracted suggestions or replace them with explicit human edits."""
    accept = approval.get("accept", [])
    edits = approval.get("edits", {})
    if not all(isinstance(item, str) for item in accept) or not isinstance(edits, dict):
        raise ValueError("Invalid approval structure")

    review_values = {field.attribute: field.value for field in review.fields if field.value is not None}
    attributes = dict(review_values)
    approvals: dict[str, str] = {}
    unresolved = set(review.action_required)
    available = {attribute.name for attribute in category.attributes}

    for attribute in accept:
        if attribute not in available:
            raise ValueError(f"Cannot accept unknown attribute {attribute!r}")
        if attribute not in review_values:
            raise ValueError(f"Cannot accept {attribute!r}; no suggested value is available")
        approvals[attribute] = "accepted"
        unresolved.discard(attribute)

    for attribute, value in edits.items():
        if attribute not in available:
            raise ValueError(f"Cannot edit unknown attribute {attribute!r}")
        attributes[attribute] = value
        approvals[attribute] = "edited"
        unresolved.discard(attribute)

    issues = tuple(
        {"attribute": issue.attribute, "code": issue.code, "message": issue.message}
        for issue in validate_local_attributes(attributes, category)
    )
    unresolved.update(issue["attribute"] for issue in issues)
    return ConfirmedProductDraft(
        category=category.key,
        attributes=attributes,
        approvals=approvals,
        action_required=tuple(sorted(unresolved)),
        local_issues=issues,
    )
