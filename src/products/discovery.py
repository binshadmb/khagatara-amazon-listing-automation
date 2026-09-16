"""Product-aware discovery of Amazon Product Type candidates."""

from dataclasses import dataclass
from typing import Any, Protocol

from src.amazon.product_types import get_product_type_client


class ProductTypeSearchClient(Protocol):
    def search_definitions_product_types(self, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class ProductTypeCandidate:
    product_type: str
    display_name: str | None = None
    marketplace_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProductTypeDiscovery:
    product_description: str
    marketplace_id: str
    candidates: tuple[ProductTypeCandidate, ...]

    @property
    def has_single_match(self) -> bool:
        return len(self.candidates) == 1

    def require_single_match(self) -> ProductTypeCandidate:
        if len(self.candidates) != 1:
            raise ValueError(
                f"Expected one product-type match for {self.product_description!r}; "
                f"Amazon returned {len(self.candidates)}. Ask the user to choose a category."
            )
        return self.candidates[0]


def discover_product_types(
    product_description: str,
    *,
    marketplace_id: str,
    locale: str = "en_IN",
    client: ProductTypeSearchClient | None = None,
) -> ProductTypeDiscovery:
    """Search Amazon for product-type candidates using a human product description.

    A product description can be a phrase such as ``Kerala Saree``. This function
    deliberately returns every Amazon candidate instead of guessing a category.
    """
    keywords = _normalise_description(product_description)
    api_client = client or get_product_type_client()
    response = api_client.search_definitions_product_types(
        marketplaceIds=[marketplace_id],
        keywords=keywords,
        locale=locale,
    )
    payload = getattr(response, "payload", response)
    if not isinstance(payload, dict):
        raise ValueError("Amazon Product Type search returned an invalid payload")

    return ProductTypeDiscovery(
        product_description=product_description,
        marketplace_id=marketplace_id,
        candidates=tuple(_extract_candidates(payload)),
    )


def _normalise_description(product_description: str) -> str:
    normalised = " ".join(product_description.split())
    if not normalised:
        raise ValueError("Product description cannot be empty")
    return normalised


def _extract_candidates(payload: dict[str, Any]) -> list[ProductTypeCandidate]:
    raw_candidates = payload.get("productTypes", payload.get("product_types", []))
    if not isinstance(raw_candidates, list):
        return []

    candidates: list[ProductTypeCandidate] = []
    for item in raw_candidates:
        if not isinstance(item, dict):
            continue
        product_type = item.get("name", item.get("productType"))
        if not isinstance(product_type, str) or not product_type:
            continue
        display_name = item.get("displayName")
        if not isinstance(display_name, str):
            display_name = None
        marketplace_ids = item.get("marketplaceIds", [])
        if not isinstance(marketplace_ids, list):
            marketplace_ids = []
        candidates.append(
            ProductTypeCandidate(
                product_type=product_type,
                display_name=display_name,
                marketplace_ids=tuple(value for value in marketplace_ids if isinstance(value, str)),
            )
        )
    return candidates
