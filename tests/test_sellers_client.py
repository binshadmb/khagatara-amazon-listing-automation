from src.amazon.client import get_sellers_client


def main() -> None:
    client = get_sellers_client()

    response = client.get_marketplace_participation()

    print("SP-API Sellers API call completed")
    print("Response received:", response is not None)

    payload = response.payload

    print("Payload received:", bool(payload))

    if payload:
        for item in payload:
            marketplace = item.get("marketplace", {})
            participation = item.get("participation", {})

            print(
                "Marketplace:",
                marketplace.get("name"),
                "| Country:",
                marketplace.get("countryCode"),
                "| Marketplace ID:",
                marketplace.get("id"),
            )

            print(
                "Store:",
                item.get("storeName"),
                "| Participating:",
                participation.get("isParticipating"),
            )


if __name__ == "__main__":
    main()