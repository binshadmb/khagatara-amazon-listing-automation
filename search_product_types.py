from sp_api.api import ProductTypeDefinitions
from sp_api.base import Marketplaces
import secure_config


def main() -> None:
    credentials = {
        "lwa_app_id": secure_config.get_client_id(),
        "lwa_client_secret": secure_config.get_client_secret(),
        "refresh_token": secure_config.get_refresh_token(),
    }

    client = ProductTypeDefinitions(
        credentials=credentials,
        marketplace=Marketplaces.IN,
    )

    response = client.search_definitions_product_types(
        marketplaceIds="A21TJRUUN4KGV",
        keywords="saree",
        locale="en_IN",
        searchLocale="en_IN",
    )

    print("Product Type Definitions API call completed")
    print("Response received:", response is not None)

    payload = response.payload or {}
    product_types = payload.get("productTypes", [])

    print("Product types returned:", len(product_types))

    for item in product_types:
        print(
            "Product Type:",
            item.get("productType"),
            "| Display name:",
            item.get("displayName"),
        )


if __name__ == "__main__":
    main()
