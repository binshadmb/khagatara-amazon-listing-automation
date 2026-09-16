"""Print a review report for a KHAGATARA local product draft."""

import argparse
import json

from src.products.attributes import load_attribute_catalog
from src.products.review import build_product_review, load_product_draft


def main() -> None:
    parser = argparse.ArgumentParser(description="Review an auto-filled KHAGATARA product draft.")
    parser.add_argument("product_file", help="Path to a local product draft JSON file")
    parser.add_argument("--category", default="kerala_saree")
    arguments = parser.parse_args()

    category = load_attribute_catalog().category(arguments.category)
    review = build_product_review(load_product_draft(arguments.product_file), category)
    print(json.dumps(review.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
