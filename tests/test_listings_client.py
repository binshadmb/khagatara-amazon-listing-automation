from src.amazon.listings import get_listings_client


def main() -> None:
    client = get_listings_client()

    response = client.get_listings_item(
        sellerId="A1TESTSELLERID",
        sku="TEST-SKU-001",
        marketplaceIds=["A21TJRUUN4KGV"],
    )

    print("LISTINGS ITEMS API CALL COMPLETED")
    print("Response received:", response is not None)
    print("Payload:", response.payload)


if __name__ == "__main__":
    main()