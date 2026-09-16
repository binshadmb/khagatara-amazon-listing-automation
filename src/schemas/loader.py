import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = PROJECT_ROOT / "data" / "schemas"


def save_schema(
    product_type: str,
    marketplace_id: str,
    schema: dict[str, Any],
) -> Path:
    """
    Save an Amazon Product Type schema locally as JSON.
    """

    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)

    safe_product_type = product_type.lower().replace("/", "_")
    safe_marketplace = marketplace_id.lower()

    path = SCHEMA_DIR / f"{safe_marketplace}_{safe_product_type}.json"

    with path.open("w", encoding="utf-8") as file:
        json.dump(schema, file, indent=2, ensure_ascii=False)

    return path


def load_schema(
    product_type: str,
    marketplace_id: str,
) -> dict[str, Any]:
    """
    Load a previously saved Product Type schema.
    """

    safe_product_type = product_type.lower().replace("/", "_")
    safe_marketplace = marketplace_id.lower()

    path = SCHEMA_DIR / f"{safe_marketplace}_{safe_product_type}.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Schema not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
