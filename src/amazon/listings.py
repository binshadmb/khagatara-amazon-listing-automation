from sp_api.api import ListingsItems
from sp_api.base.marketplaces import Marketplaces
import secure_config


def get_listings_client() -> ListingsItems:
    """
    Create an authenticated Listings Items API client.
    """

    credentials = {
        "refresh_token": secure_config.get_refresh_token(),
        "lwa_app_id": secure_config.get_client_id(),
        "lwa_client_secret": secure_config.get_client_secret(),
    }

    return ListingsItems(
        credentials=credentials,
        marketplace=Marketplaces.IN,
    )