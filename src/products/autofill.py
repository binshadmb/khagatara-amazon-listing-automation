"""Combine multiple product-data sources into a human-reviewable autofill result."""

from dataclasses import dataclass
from typing import Iterable

from src.ai.confidence import EvidenceSource, FieldSuggestion, confidence_label
from src.ai.text_analyzer import analyze_text
from src.products.attributes import ProductCategory


@dataclass(frozen=True)
class AutofillField:
    suggestion: FieldSuggestion
    alternatives: tuple[FieldSuggestion, ...] = ()

    @property
    def review_state(self) -> str:
        if self.alternatives:
            return "conflicting"
        return confidence_label(self.suggestion.confidence)


@dataclass(frozen=True)
class AutofillResult:
    category: str
    fields: dict[str, AutofillField]
    manual_fields: tuple[str, ...]

    def attributes(self) -> dict[str, object]:
        return {name: field.suggestion.value for name, field in self.fields.items()}


def autofill_product(
    *,
    category: ProductCategory,
    description: str = "",
    filename: str = "",
    suggestions: Iterable[FieldSuggestion] = (),
) -> AutofillResult:
    """Merge suggestions and flag required data that cannot be reliably inferred."""
    all_suggestions = [*suggestions]
    if description:
        all_suggestions.extend(analyze_text(description, category=category.key))
    if filename:
        all_suggestions.extend(
            analyze_text(filename, category=category.key, source=EvidenceSource.FILENAME)
        )

    fields: dict[str, AutofillField] = {}
    for attribute in category.attributes:
        candidates = [item for item in all_suggestions if item.attribute == attribute.name]
        if not candidates:
            continue
        ranked = sorted(candidates, key=lambda item: item.confidence, reverse=True)
        best = ranked[0]
        alternatives = tuple(item for item in ranked[1:] if item.value != best.value)
        fields[attribute.name] = AutofillField(best, alternatives)

    # Factual supplier data is intentionally not inferred from photos or prose.
    manual_fields = tuple(
        attribute.name
        for attribute in category.attributes
        if attribute.required and attribute.name not in fields
    )
    return AutofillResult(category=category.key, fields=fields, manual_fields=manual_fields)
