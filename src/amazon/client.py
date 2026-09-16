from sp_api.api import Sellers
from sp_api.base.marketplaces import Marketplaces
import secure_config


def get_sellers_client() -> Sellers:
    """
    Create an authenticated Amazon SP-API Sellers client.
    Credentials are retrieved through secure_config.
    """

    credentials = {
        "refresh_token": secure_config.get_refresh_token(),
        "lwa_app_id": secure_config.get_client_id(),
        "lwa_client_secret": secure_config.get_client_secret(),
    }

    return Sellers(
        credentials=credentials,
        marketplace=Marketplaces.IN,
    )