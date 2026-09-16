import httpx
import secure_config


def main() -> None:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": secure_config.get_refresh_token(),
        "client_id": secure_config.get_client_id(),
        "client_secret": secure_config.get_client_secret(),
    }

    response = httpx.post(
        "https://api.amazon.com/auth/o2/token",
        data=data,
        timeout=30.0,
    )

    print("HTTP status:", response.status_code)

    body = response.json()

    if response.is_success:
        print("LWA authentication: SUCCESS")
        print("Token type:", body.get("token_type"))
        print("Expires in:", body.get("expires_in"), "seconds")
        print("Access token received:", bool(body.get("access_token")))
    else:
        print("LWA authentication: FAILED")
        print("Error:", body.get("error"))
        print("Description:", body.get("error_description"))


if __name__ == "__main__":
    main()
