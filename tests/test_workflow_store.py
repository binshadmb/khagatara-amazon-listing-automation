import tempfile
import unittest

from src.products.workflow_store import ProductWorkflowStore


class ProductWorkflowStoreTests(unittest.TestCase):
    def test_persists_approval_record_across_store_instances(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            saved = ProductWorkflowStore(temporary).save(
                "women_kurti_draft_example",
                {
                    "category": "women_kurti",
                    "status": "Ready for Amazon",
                    "approvals": {"colour": "accepted"},
                    "attributes": {"colour": "Blue"},
                    "actionRequired": [],
                    "localIssues": [],
                },
            )
            loaded = ProductWorkflowStore(temporary).load("women_kurti_draft_example")
            self.assertEqual(loaded["id"], "women_kurti_draft_example")
            self.assertEqual(loaded["status"], "Ready for Amazon")
            self.assertEqual(loaded["approvals"], {"colour": "accepted"})
            self.assertTrue(saved["updatedAt"])

    def test_rejects_a_product_id_that_can_escape_the_store(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "simple file name"):
                ProductWorkflowStore(temporary).save("../outside", {})
