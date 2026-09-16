"""Conservative local category detection from product text."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryCandidate:
    category: str
    confidence: float
    evidence: str


def detect_categories(text: str) -> list[CategoryCandidate]:
    """Return category suggestions; caller must confirm ambiguous results."""
    value = text.casefold()
    candidates: list[CategoryCandidate] = []
    if "kerala saree" in value or "kasavu" in value:
        candidates.append(CategoryCandidate("kerala_saree", 0.90, "kerala saree/kasavu"))
    elif "saree" in value or "sari" in value:
        candidates.append(CategoryCandidate("saree", 0.86, "saree/sari"))
    if "kurti" in value:
        candidates.append(CategoryCandidate("women_kurti", 0.92, "kurti"))
    elif "ladies top" in value or "women top" in value or "womens top" in value:
        candidates.append(CategoryCandidate("women_top", 0.88, "top"))
    return candidates
