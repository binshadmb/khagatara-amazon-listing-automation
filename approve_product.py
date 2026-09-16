"""Create a confirmed product draft from review data and an approval file."""

import argparse
import json

from src.products.approval import apply_approvals, load_approval_file
from src.products.attributes import load_attribute_catalog
from src.products.review import build_product_review, load_product_draft


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply product-review confirmations and edits.")
    parser.add_argument("product_file")
    parser.add_argument("approval_file")
    parser.add_argument("--category", default="kerala_saree")
    arguments = parser.parse_args()
    category = load_attribute_catalog().category(arguments.category)
    review = build_product_review(load_product_draft(arguments.product_file), category)
    confirmed = apply_approvals(review, category, load_approval_file(arguments.approval_file))
    print(json.dumps(confirmed.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
