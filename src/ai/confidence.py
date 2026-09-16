"""Confidence-scored, reviewable product attribute suggestions."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EvidenceSource(str, Enum):
    DESCRIPTION = "description"
    FILENAME = "filename"
    IMAGE = "image"
    SUPPLIER_CATALOG = "supplier_catalog"
    MANUAL = "manual"


@dataclass(frozen=True)
class FieldSuggestion:
    attribute: str
    value: Any
    confidence: float
    source: EvidenceSource
    evidence: str

    @property
    def needs_review(self) -> bool:
        return self.confidence < 0.9 or self.source is EvidenceSource.IMAGE


def confidence_label(confidence: float) -> str:
    if confidence >= 0.9:
        return "high"
    if confidence >= 0.7:
        return "medium"
    return "needs_confirmation"
