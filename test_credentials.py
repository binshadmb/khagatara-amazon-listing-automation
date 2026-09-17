import secure_config

def main():
    client_id = secure_config.get_client_id()
    client_secret = secure_config.get_client_secret()
    refresh_token = secure_config.get_refresh_token()

    print("Client ID loaded:", bool(client_id))
    print("Client ID length:", len(client_id))

    print("Client Secret loaded:", bool(client_secret))
    print("Client Secret length:", len(client_secret))

    print("Refresh Token loaded:", bool(refresh_token))
    print("Refresh Token length:", len(refresh_token))

    print("Refresh Token starts with:", refresh_token[:10] + "..." if refresh_token else "EMPTY")

if __name__ == "__main__":
    main()