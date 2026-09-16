from src.amazon.product_types import get_product_type_client


def main() -> None:
    client = get_product_type_client()

    response = client.search_definitions_product_types(
        marketplaceIds=["A21TJRUUN4KGV"],
        keywords="saree",
        locale="en_IN",
    )

    print("PRODUCT TYPE SEARCH COMPLETED")
    print("Response received:", response is not None)

    print("Payload:")
    print(response.payload)


if __name__ == "__main__":
    main()