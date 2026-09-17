import io
import tempfile
import unittest
from pathlib import Path
from fastapi import HTTPException
from fastapi.datastructures import UploadFile

from src import api
from src.products.workflow_store import ProductWorkflowStore


class UploadTests(unittest.IsolatedAsyncioTestCase):
    async def test_upload_source_stores_file_and_returns_metadata(self) -> None:
        original_uploads = api.UPLOADS_DIR
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                api.UPLOADS_DIR = Path(temp_dir)
                test_file = UploadFile(
                    filename="sample_product.txt",
                    file=io.BytesIO(b"Sample product text description"),
                    headers={"content-type": "text/plain"},
                )

                res = await api.upload_source(test_file)

                self.assertEqual(res["filename"], "sample_product.txt")
                self.assertEqual(res["contentType"], "text/plain")
                self.assertEqual(res["size"], 31)
                self.assertEqual(res["status"], "uploaded")
                self.assertTrue((api.UPLOADS_DIR / res["storedFilename"]).exists())
        finally:
            api.UPLOADS_DIR = original_uploads

    async def test_upload_source_rejects_disallowed_extension(self) -> None:
        test_file = UploadFile(
            filename="malicious.exe",
            file=io.BytesIO(b"binary"),
        )
        with self.assertRaises(HTTPException) as raised:
            await api.upload_source(test_file)
        self.assertEqual(raised.exception.status_code, 422)

    def test_create_product_associates_upload_id(self) -> None:
        original_uploads = api.UPLOADS_DIR
        original_products = api.PRODUCTS_DIR
        original_store = api.WORKFLOW_STORE
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                api.UPLOADS_DIR = temp_path / "uploads"
                api.PRODUCTS_DIR = temp_path / "products"
                api.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
                api.PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
                api.WORKFLOW_STORE = ProductWorkflowStore(api.PRODUCTS_DIR / "workflow_state")

                # Create fake stored upload file
                upload_id = "testupload123456"
                upload_file = api.UPLOADS_DIR / f"{upload_id}.txt"
                upload_file.write_text("Kerala saree description", encoding="utf-8")

                request = api.ProductCreateRequest(
                    name="Test Associated Product",
                    category="kerala_saree",
                    description="Cream saree description",
                    upload_id=upload_id,
                )

                created = api.create_product(request)

                self.assertIsNotNone(created["id"])
                self.assertEqual(created["category"], "kerala_saree")

                # Test ingestion of source file via product_id
                ingested = api.ingest_product_source(created["id"])
                self.assertEqual(ingested["upload_id"], upload_id)
                self.assertIn("saree description", ingested["ingestion"]["text"])
        finally:
            api.UPLOADS_DIR = original_uploads
            api.PRODUCTS_DIR = original_products
            api.WORKFLOW_STORE = original_store

    def test_autofill_from_ingested_source_file(self) -> None:
        original_uploads = api.UPLOADS_DIR
        original_products = api.PRODUCTS_DIR
        original_store = api.WORKFLOW_STORE
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                api.UPLOADS_DIR = temp_path / "uploads"
                api.PRODUCTS_DIR = temp_path / "products"
                api.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
                api.PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
                api.WORKFLOW_STORE = ProductWorkflowStore(api.PRODUCTS_DIR / "workflow_state")

                upload_id = "autofilltest99"
                upload_file = api.UPLOADS_DIR / f"{upload_id}.txt"
                upload_file.write_text("Kerala cotton kasavu saree with golden peacock border", encoding="utf-8")

                request = api.ProductCreateRequest(
                    name="Ingestion Autofill Product",
                    category="kerala_saree",
                    upload_id=upload_id,
                )

                created = api.create_product(request)

                fabric_field = next(f for f in created["fields"] if f["attribute"] == "fabric_type")
                self.assertEqual(fabric_field["value"], "Kerala Cotton")
        finally:
            api.UPLOADS_DIR = original_uploads
            api.PRODUCTS_DIR = original_products
            api.WORKFLOW_STORE = original_store


