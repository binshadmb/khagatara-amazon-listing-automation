"""Deterministic text and filename extraction for product autofill."""

import re

from src.ai.confidence import EvidenceSource, FieldSuggestion


_KERALA_SAREE_RULES: tuple[tuple[str, str, str], ...] = (
    ("fabric_type", "kerala cotton", "Kerala Cotton"),
    ("fabric_type", "cotton silk", "Cotton Silk"),
    ("fabric_type", "tissue cotton", "Tissue Cotton"),
    ("fabric_type", "handloom cotton", "Handloom Cotton"),
    ("fabric_type", "cotton", "Cotton"),
    ("fabric_type", "silk", "Silk"),
    ("fabric_type", "tissue", "Tissue"),
    ("body_colour", "off white", "Off White"),
    ("body_colour", "rose gold", "Rose Gold"),
    ("body_colour", "cream", "Cream"),
    ("body_colour", "ivory", "Ivory"),
    ("body_colour", "white", "White"),
    ("border_colour", "rose gold border", "Rose Gold"),
    ("border_colour", "golden border", "Gold"),
    ("border_colour", "gold border", "Gold"),
    ("border_type", "no border", "No Border"),
    ("border_type", "contrast border", "Contrast Border"),
    ("border_type", "kasavu border", "Kasavu"),
    ("border_width", "0.5 inch", "0.5 inch"),
    ("border_width", "1 inch", "1 inch"),
    ("border_width", "1.5 inch", "1.5 inch"),
    ("border_width", "2 inch", "2 inch"),
    ("border_width", "2.5 inch", "2.5 inch"),
    ("border_width", "3 inch", "3 inch"),
    ("motif", "peacock", "Peacock"),
    ("motif", "kathakali", "Kathakali"),
    ("motif", "temple", "Temple"),
    ("motif", "floral", "Floral"),
    ("motif", "paisley", "Paisley"),
    ("work", "zari", "Zari Work"),
    ("work", "kasavu", "Kasavu"),
    ("work", "tissue work", "Tissue Work"),
    ("work", "woven", "Woven Work"),
    ("pattern", "printed", "Printed"),
    ("pattern", "woven", "Woven"),
    ("occasion", "onam", "Onam"),
    ("occasion", "wedding", "Wedding"),
    ("occasion", "festival", "Festival"),
)

_BORDER_COLOUR_PATTERNS: tuple[tuple[str, str], ...] = (
    ("rose gold", "Rose Gold"),
    ("golden", "Gold"),
    ("gold", "Gold"),
    ("silver", "Silver"),
    ("copper", "Copper"),
)


def analyze_text(text: str, *, category: str, source: EvidenceSource = EvidenceSource.DESCRIPTION) -> list[FieldSuggestion]:
    """Extract deterministic hints from human-readable product text.

    It produces suggestions, never claimed facts: all text-derived values remain
    reviewable unless confirmed by a supplier record or a user.
    """
    normalised = re.sub(r"[-_/]+", " ", text.casefold())
    if category in {"women_kurti", "women_top"}:
        return _analyze_top_or_kurti(normalised, category, source)
    if category not in {"kerala_saree", "saree"}:
        return []
    suggestions: list[FieldSuggestion] = []
    used_attributes: set[str] = set()
    for attribute, phrase, value in _KERALA_SAREE_RULES:
        if attribute not in used_attributes and phrase in normalised:
            suggestions.append(
                FieldSuggestion(attribute, value, 0.86, source, phrase)
            )
            used_attributes.add(attribute)
    if "border_colour" not in used_attributes:
        for phrase, value in _BORDER_COLOUR_PATTERNS:
            # Allows natural phrases such as "golden peacock border" while
            # avoiding a bare colour word elsewhere in the description.
            if re.search(rf"\b{re.escape(phrase)}\b(?:\s+\w+){{0,3}}\s+border\b", normalised):
                suggestions.append(FieldSuggestion("border_colour", value, 0.82, source, f"{phrase} ... border"))
                break
    return suggestions


def _analyze_top_or_kurti(
    text: str,
    category: str,
    source: EvidenceSource,
) -> list[FieldSuggestion]:
    rules = [
        ("fabric_type", "cotton", "Cotton"),
        ("fabric_type", "rayon", "Rayon"),
        ("fabric_type", "viscose", "Viscose"),
        ("fabric_type", "linen", "Linen"),
        ("sleeve_length", "sleeveless", "Sleeveless"),
        ("sleeve_length", "short sleeve", "Short Sleeve"),
        ("sleeve_length", "three quarter", "Three Quarter Sleeve"),
        ("sleeve_length", "full sleeve", "Full Sleeve"),
        ("garment_length", "long", "Long"),
        ("garment_length", "short", "Short"),
        ("garment_length", "regular", "Regular"),
        ("neck_style", "round neck", "Round Neck"),
        ("neck_style", "v neck", "V Neck"),
        ("neck_style", "mandarin collar", "Mandarin Collar"),
        ("pattern", "floral", "Floral"),
        ("pattern", "printed", "Printed"),
        ("pattern", "striped", "Striped"),
    ]
    suggestions: list[FieldSuggestion] = []
    used: set[str] = set()
    for attribute, phrase, value in rules:
        if attribute not in used and phrase in text:
            suggestions.append(FieldSuggestion(attribute, value, 0.86, source, phrase))
            used.add(attribute)
    for colour in ("off white", "cream", "white", "black", "blue", "green", "red", "pink", "yellow"):
        if colour in text:
            suggestions.append(FieldSuggestion("colour", colour.title(), 0.84, source, colour))
            break
    return suggestions
