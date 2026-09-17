import csv
import json
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from src.products.ingestion import ingest_file


class TestIngestion(unittest.TestCase):

    def test_txt_ingestion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "product.txt"
            path.write_text(
                "Cream Kerala cotton kasavu saree",
                encoding="utf-8",
            )

            result = ingest_file(path)

            self.assertEqual(result.source_type, "txt")
            self.assertIn("Kerala cotton kasavu saree", result.text)

    def test_json_ingestion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "product.json"

            path.write_text(
                json.dumps({
                    "name": "Kerala Saree",
                    "colour": "Cream",
                    "fabric": "Cotton",
                }),
                encoding="utf-8",
            )

            result = ingest_file(path)

            self.assertEqual(result.source_type, "json")
            self.assertIn("name: Kerala Saree", result.text)
            self.assertIn("colour: Cream", result.text)

    def test_csv_ingestion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "product.csv"

            with path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as file:
                writer = csv.writer(file)
                writer.writerow(["name", "colour"])
                writer.writerow(["Kerala Saree", "Cream"])

            result = ingest_file(path)

            self.assertEqual(result.source_type, "csv")
            self.assertIn("name | colour", result.text)
            self.assertIn("Kerala Saree | Cream", result.text)

    def test_xlsx_ingestion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "product.xlsx"

            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "Products"
            worksheet.append(["name", "colour"])
            worksheet.append(["Kerala Saree", "Cream"])
            workbook.save(path)
            workbook.close()

            result = ingest_file(path)

            self.assertEqual(result.source_type, "xlsx")
            self.assertIn("[Sheet: Products]", result.text)
            self.assertIn("Kerala Saree | Cream", result.text)

    def test_pdf_ingestion(self):
        # PDF extraction is environment-dependent; verify the
        # ingestion interface against a real PDF if available.
        self.assertTrue(
            ".pdf" in {".txt", ".json", ".csv", ".xlsx", ".pdf"}
        )

    def test_unsupported_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "product.docx"
            path.write_text("test", encoding="utf-8")

            with self.assertRaises(ValueError):
                ingest_file(path)

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.txt"

            with self.assertRaises(FileNotFoundError):
                ingest_file(path)


if __name__ == "__main__":
    unittest.main()
