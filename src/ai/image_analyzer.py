"""Contract for future image-analysis providers; no provider is hard-coded."""

from pathlib import Path
from typing import Protocol

from src.ai.confidence import FieldSuggestion


class ImageAnalyzer(Protocol):
    def analyze(self, image_path: Path, category: str) -> list[FieldSuggestion]:
        """Return visible-feature suggestions only; never infer factual supplier data."""
        ...
