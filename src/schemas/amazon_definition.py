from typing import Any

from src.amazon.product_types import (
    get_definition_with_retry,
    get_product_type_client,
)
from src.schemas.loader import save_schema


def fetch_and_save_definition(
    product_type: str,
    marketplace_id: str,
    locale: str = "en_IN",
    requirements: str = "LISTING",
) -> str:
    client = get_product_type_client()

    response = get_definition_with_retry(
        client,
        product_type=product_type,
        marketplace_id=marketplace_id,
        locale=locale,
        requirements=requirements,
    )

    payload: dict[str, Any] = response.payload

    path = save_schema(
        product_type=product_type,
        marketplace_id=marketplace_id,
        schema=payload,
    )

    return str(path)
