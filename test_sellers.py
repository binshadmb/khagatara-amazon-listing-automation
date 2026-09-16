from sp_api.api import Sellers
from sp_api.base import Marketplaces
import secure_config


def main() -> None:
    credentials = {
        "lwa_app_id": secure_config.get_client_id(),
        "lwa_client_secret": secure_config.get_client_secret(),
        "refresh_token": secure_config.get_refresh_token(),
    }

    client = Sellers(
        credentials=credentials,
        marketplace=Marketplaces.IN,
    )

    response = client.get_marketplace_participation()

    print("SP-API Sellers API call completed")
    print("Response received:", response is not None)
    print("Payload received:", bool(response.payload))

    if response.payload:
        for item in response.payload:
            marketplace = item.get("marketplace", {})
            print(
                "Marketplace:",
                marketplace.get("name"),
                "|",
                marketplace.get("countryCode"),
                "|",
                marketplace.get("id"),
            )


if __name__ == "__main__":
    main()
