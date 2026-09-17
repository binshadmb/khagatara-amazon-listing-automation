import requests
import secure_config


def main():
    client_id = secure_config.get_client_id()
    client_secret = secure_config.get_client_secret()
    refresh_token = secure_config.get_refresh_token()

    # Get a fresh LWA access token
    token_response = requests.post(
        "https://api.amazon.com/auth/o2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )

    token_response.raise_for_status()
    access_token = token_response.json()["access_token"]

    # Direct SP-API request
    url = "https://sandbox.sellingpartnerapi-eu.amazon.com/definitions/2020-09-01/productTypes"

    params = {
        "marketplaceIds": "A21TJRUUN4KGV",
        "keywords": "saree",
        "locale": "en_IN",
        "searchLocale": "en_IN",
    }

    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json",
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=30,
    )

    print("HTTP status:", response.status_code)
    print("Request URL:", response.url)
    print("Amazon request ID:", response.headers.get("x-amzn-RequestId"))

    try:
        data = response.json()
        print("Response:")
        print(data)
    except Exception:
        print("Raw response:")
        print(response.text)


if __name__ == "__main__":
    main()