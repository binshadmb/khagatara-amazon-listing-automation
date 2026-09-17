import requests
import secure_config


def main():
    client_id = secure_config.get_client_id()
    client_secret = secure_config.get_client_secret()
    refresh_token = secure_config.get_refresh_token()

    response = requests.post(
        "https://api.amazon.com/auth/o2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )

    print("HTTP status:", response.status_code)

    try:
        data = response.json()
    except Exception:
        print("Response was not JSON:")
        print(response.text)
        return

    print("Response keys:", list(data.keys()))

    if response.ok:
        access_token = data.get("access_token", "")
        print("Access token received:", bool(access_token))
        print("Access token length:", len(access_token))
        print("Token type:", data.get("token_type"))
        print("Expires in:", data.get("expires_in"))
    else:
        print("Amazon error:", data.get("error"))
        print("Amazon error description:", data.get("error_description"))


if __name__ == "__main__":
    main()