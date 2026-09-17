"""Durable local storage for product review and approval workflow state."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ProductWorkflowStore:
    """Persist one JSON workflow record per product using atomic replacement."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def load(self, product_id: str) -> dict[str, Any] | None:
        path = self._path(product_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as file:
            record = json.load(file)
        if not isinstance(record, dict):
            raise ValueError(f"Workflow record for {product_id!r} must be an object")
        return record

    def save(self, product_id: str, record: dict[str, Any]) -> dict[str, Any]:
        if not product_id or Path(product_id).name != product_id:
            raise ValueError("Product id must be a simple file name")
        self.directory.mkdir(parents=True, exist_ok=True)
        saved = dict(record)
        saved["id"] = product_id
        saved["updatedAt"] = datetime.now(timezone.utc).isoformat()
        destination = self._path(product_id)
        temporary = destination.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            json.dump(saved, file, indent=2, ensure_ascii=False)
            file.write("\n")
        temporary.replace(destination)
        return saved

    def _path(self, product_id: str) -> Path:
        return self.directory / f"{product_id}.json"
