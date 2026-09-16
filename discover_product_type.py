"""Run Amazon Product Type discovery from the command line."""

import argparse

from src.products.discovery import discover_product_types


MARKETPLACE_IN = "A21TJRUUN4KGV"


def main() -> None:
    parser = argparse.ArgumentParser(description="Find Amazon product types for a product description.")
    parser.add_argument("product_description", help='Example: "Kerala Saree"')
    parser.add_argument("--marketplace-id", default=MARKETPLACE_IN)
    arguments = parser.parse_args()

    result = discover_product_types(
        arguments.product_description,
        marketplace_id=arguments.marketplace_id,
    )
    if not result.candidates:
        print("No Amazon Product Type candidates were returned.")
        return

    print(f"Amazon candidates for: {result.product_description}")
    for candidate in result.candidates:
        name = f" - {candidate.display_name}" if candidate.display_name else ""
        print(f" - {candidate.product_type}{name}")


if __name__ == "__main__":
    main()
