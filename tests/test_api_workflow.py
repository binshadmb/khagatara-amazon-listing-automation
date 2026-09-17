import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from src import api
from src.products.workflow_store import ProductWorkflowStore


class ApiWorkflowTests(unittest.TestCase):
    def test_approval_is_returned_after_a_later_product_read(self) -> None:
        original_store = api.WORKFLOW_STORE
        try:
            with tempfile.TemporaryDirectory() as temporary:
                api.WORKFLOW_STORE = ProductWorkflowStore(temporary)
                approved = api.approve_product(
                    "women_kurti_draft_example",
                    api.ApprovalRequest(
                        accept=[
                            "fabric_type",
                            "colour",
                            "pattern",
                            "neck_style",
                            "sleeve_length",
                        ],
                        edits={"garment_length": "Long"},
                    ),
                )
                loaded = api.product("women_kurti_draft_example")

                self.assertEqual(approved["status"], "Ready for Amazon")
                self.assertEqual(loaded["status"], "Ready for Amazon")
                self.assertEqual(loaded["actionRequired"], [])
                self.assertEqual(
                    next(field for field in loaded["fields"] if field["attribute"] == "garment_length")["review_state"],
                    "edited",
                )
                generated = api.generate_product_variants(
                    "women_kurti_draft_example",
                    api.VariantRequest(
                        base_sku="KURTI-BLUE",
                        dimensions=[
                            api.VariantDimensionRequest(
                                attribute="size",
                                options=[
                                    api.VariantOptionRequest(value="M", code="M"),
                                    api.VariantOptionRequest(value="L", code="L"),
                                ],
                            )
                        ],
                    ),
                )
                self.assertEqual([item["sku"] for item in generated["variants"]], ["KURTI-BLUE-M", "KURTI-BLUE-L"])
        finally:
            api.WORKFLOW_STORE = original_store

    def test_mapping_rejects_the_unapproved_saree_profile(self) -> None:
        original_store = api.WORKFLOW_STORE
        try:
            with tempfile.TemporaryDirectory() as temporary:
                api.WORKFLOW_STORE = ProductWorkflowStore(temporary)
                api.WORKFLOW_STORE.save(
                    "kerala_saree_draft_example",
                    {
                        "category": "kerala_saree",
                        "status": "Ready for Amazon",
                        "attributes": {"title": "Kasavu Saree"},
                        "approvals": {},
                        "actionRequired": [],
                        "localIssues": [],
                    },
                )

                with self.assertRaises(HTTPException) as raised:
                    api.map_product_to_amazon(
                        "kerala_saree_draft_example",
                        api.MappingRequest(
                            profile="kerala_saree_draft.json",
                            product_type="LUGGAGE",
                            marketplace_id="A21TJRUUN4KGV",
                        ),
                    )

                self.assertEqual(raised.exception.status_code, 422)
                self.assertIn("approved mapping profile", str(raised.exception.detail))
        finally:
            api.WORKFLOW_STORE = original_store

    def test_validation_returns_a_structured_required_field_report(self) -> None:
        original_store = api.WORKFLOW_STORE
        original_load_schema = api.load_schema
        try:
            with tempfile.TemporaryDirectory() as temporary:
                api.WORKFLOW_STORE = ProductWorkflowStore(temporary)
                api.load_schema = lambda *_args: {
                    "schema": {
                        "properties": {"item_name": {"type": "array"}},
                        "required": ["item_name"],
                    }
                }
                api.WORKFLOW_STORE.save(
                    "validated-product",
                    {
                        "category": "women_kurti",
                        "status": "Ready for Amazon",
                        "attributes": {},
                        "approvals": {},
                        "actionRequired": [],
                        "localIssues": [],
                        "mapping": {
                            "productType": "APPAREL",
                            "marketplaceId": "A21TJRUUN4KGV",
                            "attributes": {},
                        },
                    },
                )

                result = api.validate_product_mapping("validated-product")

                self.assertFalse(result["valid"])
                self.assertEqual(result["issues"][0]["field"], "item_name")
                self.assertEqual(result["issues"][0]["code"], "REQUIRED")
        finally:
            api.WORKFLOW_STORE = original_store
            api.load_schema = original_load_schema

    def test_preview_returns_a_listing_payload_without_submission(self) -> None:
        original_store = api.WORKFLOW_STORE
        original_load_schema = api.load_schema
        try:
            with tempfile.TemporaryDirectory() as temporary:
                api.WORKFLOW_STORE = ProductWorkflowStore(temporary)
                api.load_schema = lambda *_args: {
                    "schema": {
                        "properties": {"item_name": {"type": "array"}},
                        "required": ["item_name"],
                    }
                }
                api.WORKFLOW_STORE.save(
                    "preview-product",
                    {
                        "category": "women_kurti",
                        "status": "Ready for Amazon",
                        "attributes": {},
                        "approvals": {},
                        "actionRequired": [],
                        "localIssues": [],
                        "mapping": {
                            "productType": "APPAREL",
                            "marketplaceId": "A21TJRUUN4KGV",
                            "attributes": {"item_name": [{"value": "Blue Kurti"}]},
                        },
                    },
                )

                result = api.preview_listing_payload(
                    "preview-product",
                    api.PreviewRequest(sku="KURTI-BLUE-M"),
                )

                self.assertTrue(result["valid"])
                self.assertEqual(result["payload"]["sku"], "KURTI-BLUE-M")
                self.assertEqual(result["payload"]["productType"], "APPAREL")
                self.assertEqual(result["payload"]["attributes"]["item_name"][0]["value"], "Blue Kurti")
        finally:
            api.WORKFLOW_STORE = original_store
            api.load_schema = original_load_schema

    def test_submission_does_not_call_amazon_when_final_validation_fails(self) -> None:
        original_store = api.WORKFLOW_STORE
        original_load_schema = api.load_schema
        original_client = api.get_listings_client
        try:
            with tempfile.TemporaryDirectory() as temporary, patch.dict("os.environ", {"AWS_ENV": "SANDBOX"}):
                api.WORKFLOW_STORE = ProductWorkflowStore(temporary)
                api.load_schema = lambda *_args: {
                    "schema": {
                        "properties": {"item_name": {"type": "array"}},
                        "required": ["item_name"],
                    }
                }
                api.get_listings_client = lambda: self.fail("Listings client must not be called")
                api.WORKFLOW_STORE.save(
                    "blocked-submission",
                    {
                        "category": "women_kurti",
                        "status": "Ready for Amazon",
                        "attributes": {},
                        "approvals": {},
                        "actionRequired": [],
                        "localIssues": [],
                        "mapping": {
                            "productType": "APPAREL",
                            "marketplaceId": "A21TJRUUN4KGV",
                            "attributes": {},
                        },
                    },
                )

                with self.assertRaises(HTTPException) as raised:
                    api.submit_product_listing(
                        "blocked-submission",
                        api.SubmissionRequest(
                            seller_id="A1TESTSELLERID",
                            sku="BLOCKED-SKU",
                            environment="sandbox",
                        ),
                    )

                self.assertEqual(raised.exception.status_code, 422)
                self.assertIn("Submission blocked by validation", str(raised.exception.detail))
        finally:
            api.WORKFLOW_STORE = original_store
            api.load_schema = original_load_schema
            api.get_listings_client = original_client
