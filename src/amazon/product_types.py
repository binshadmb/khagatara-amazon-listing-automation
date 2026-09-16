import logging
import time
from collections.abc import Callable
from typing import Any

import httpx
from sp_api.api import ProductTypeDefinitions
from sp_api.base.marketplaces import Marketplaces
import secure_config

logger = logging.getLogger(__name__)


def get_product_type_client() -> ProductTypeDefinitions:
    credentials = {
        "refresh_token": secure_config.get_refresh_token(),
        "lwa_app_id": secure_config.get_client_id(),
        "lwa_client_secret": secure_config.get_client_secret(),
    }

    return ProductTypeDefinitions(
        credentials=credentials,
        marketplace=Marketplaces.IN,
    )


def get_definition_with_retry(
    client: ProductTypeDefinitions,
    *,
    product_type: str,
    marketplace_id: str,
    locale: str = "en_IN",
    requirements: str = "LISTING",
    max_attempts: int = 4,
    initial_backoff_seconds: float = 2.0,
    sleep: Callable[[float], None] = time.sleep,
) -> Any:
    """Fetch a product definition, retrying transient network failures only.

    Authentication and API validation failures are deliberately not retried. They
    require a configuration or payload correction rather than another request.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    for attempt in range(1, max_attempts + 1):
        try:
            return client.get_definitions_product_type(
                productType=product_type,
                marketplaceIds=[marketplace_id],
                locale=locale,
                requirements=requirements,
            )
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as error:
            if attempt == max_attempts:
                raise

            delay = initial_backoff_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Product definition request failed (%s/%s): %s. Retrying in %.1fs.",
                attempt,
                max_attempts,
                type(error).__name__,
                delay,
            )
            sleep(delay)
