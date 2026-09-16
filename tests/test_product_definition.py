from src.schemas.amazon_definition import fetch_and_save_definition


def main() -> None:
    path = fetch_and_save_definition(
        product_type="LUGGAGE",
        marketplace_id="A21TJRUUN4KGV",
    )
    print("PRODUCT TYPE DEFINITION SAVED")
    print("Schema path:", path)


if __name__ == "__main__":
    main()
