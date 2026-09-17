from __future__ import annotations

import os
from pathlib import Path
import json
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.products.attributes import load_attribute_catalog
from src.products.ingestion import ingest_file
from src.products.approval import apply_approvals
from src.products.listing_payload import build_listing_payload
from src.products.review import build_product_review, load_product_draft
from src.products.variants import VariantDimension, VariantOption, generate_variants
from src.products.workflow_store import ProductWorkflowStore
from src.amazon.listings import get_listings_client
from src.schemas.loader import load_schema
from src.schemas.mapping_profiles import DEFAULT_PROFILE_DIR, load_mapping_profile, map_with_profile
from src.schemas.parser import parse_amazon_definition
from src.validation.schema_validator import validate_attributes


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_DIR = PROJECT_ROOT / "data" / "products"
UPLOADS_DIR = PROJECT_ROOT / "data" / "uploads"
WORKFLOW_STORE = ProductWorkflowStore(PRODUCTS_DIR / "workflow_state")

ALLOWED_UPLOAD_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".pdf",
    ".csv",
    ".xlsx",
    ".json",
    ".txt",
}

MAX_UPLOAD_SIZE = 25 * 1024 * 1024


app = FastAPI(
    title="KHAGATARA Amazon Listing Automation API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductCreateRequest(BaseModel):
    name: str = ""
    category: str
    description: str = ""
    filename: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)
    upload_id: str | None = None


class ApprovalRequest(BaseModel):
    accept: list[str] = Field(default_factory=list)
    edits: dict[str, Any] = Field(default_factory=dict)


class VariantOptionRequest(BaseModel):
    value: str
    code: str


class VariantDimensionRequest(BaseModel):
    attribute: str
    options: list[VariantOptionRequest]


class VariantRequest(BaseModel):
    base_sku: str
    dimensions: list[VariantDimensionRequest] = Field(default_factory=list)
    excluded_combinations: list[dict[str, str]] = Field(default_factory=list)


class MappingRequest(BaseModel):
    profile: str
    product_type: str
    marketplace_id: str


class PreviewRequest(BaseModel):
    sku: str
    requirements: str = "LISTING"


class SubmissionRequest(PreviewRequest):
    seller_id: str
    environment: str


def _catalog():
    return load_attribute_catalog()


def _draft_files() -> list[Path]:
    return sorted(
        path
        for path in PRODUCTS_DIR.glob("*_draft*.json")
        if path.name != "attribute_catalog.json"
    )


def _product_id(path: Path) -> str:
    return path.stem


def _mapping_profile_path(profile_name: str) -> Path:
    candidate = Path(profile_name)
    if candidate.name != profile_name or candidate.suffix != ".json":
        raise ValueError("Mapping profile must be a JSON file name")
    return DEFAULT_PROFILE_DIR / candidate.name


def _category_key(draft: dict[str, Any], path: Path) -> str:
    category_key = draft.get("category")
    if isinstance(category_key, str) and category_key:
        return category_key

    from src.products.category_detection import detect_categories

    text = " ".join(
        value
        for value in (
            draft.get("description", ""),
            draft.get("filename", ""),
            draft.get("attributes", {}).get("title", ""),
        )
        if isinstance(value, str)
    )
    candidates = detect_categories(text)
    if not candidates:
        raise ValueError(f"Unable to determine category for {path.name}")
    return candidates[0].category


def _approved_product(record: dict[str, Any]) -> dict[str, Any]:
    attributes = record.get("attributes", {})
    approvals = record.get("approvals", {})
    if not isinstance(attributes, dict) or not isinstance(approvals, dict):
        raise ValueError("Stored workflow record is invalid")
    stored_fields = record.get("fields")
    fields = stored_fields if isinstance(stored_fields, list) else [
        {
            "attribute": name,
            "value": value,
            "source": "manual" if approvals.get(name) in {"accepted", "edited"} else "existing",
            "confidence": 1.0 if approvals.get(name) in {"accepted", "edited"} else None,
            "review_state": approvals.get(name, "manual"),
        }
        for name, value in attributes.items()
    ]
    return {
        "id": record["id"],
        "name": attributes.get("title") or record["id"],
        "category": record["category"],
        "status": record["status"],
        "updatedAt": record["updatedAt"],
        "fields": fields,
        "actionRequired": record.get("actionRequired", []),
        "localIssues": record.get("localIssues", []),
    }


def _build_product(path: Path) -> dict[str, Any]:
    persisted = WORKFLOW_STORE.load(_product_id(path))
    if persisted is not None:
        return _approved_product(persisted)

    draft = load_product_draft(path)
    category_key = _category_key(draft, path)

    catalog = _catalog()
    category = catalog.category(category_key)

    review = build_product_review(draft, category, uploads_dir=UPLOADS_DIR)

    attributes = {
        field.attribute: field.value
        for field in review.fields
        if field.value is not None
    }

    title = (
        attributes.get("title")
        or draft.get("name")
        or draft.get("description")
        or path.stem
    )

    if not isinstance(title, str):
        title = path.stem

    status = (
        "Ready for Amazon"
        if review.is_ready_for_mapping
        else "Review required"
    )

    return {
        "id": _product_id(path),
        "name": title,
        "category": category_key,
        "status": status,
        "updatedAt": "Local draft",
        "fields": [
            {
                "attribute": field.attribute,
                "value": field.value,
                "source": field.source,
                "confidence": field.confidence,
                "review_state": field.review_state,
            }
            for field in review.fields
        ],
        "actionRequired": list(review.action_required),
        "localIssues": [
            issue.message
            for issue in review.local_issues
        ],
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/categories")
def categories() -> dict[str, list[dict[str, str]]]:
    catalog = _catalog()

    return {
        "categories": [
            {
                "id": category.key,
                "name": category.display_name,
            }
            for category in catalog.categories.values()
        ]
    }


@app.post("/api/products", status_code=201)
def create_product(request: ProductCreateRequest) -> dict[str, Any]:
    """Create a new local product draft for the listing workflow."""

    category_key = request.category.strip()
    if not category_key:
        raise HTTPException(status_code=422, detail="Product category is required")

    try:
        category = _catalog().category(category_key)
    except (KeyError, ValueError) as error:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown product category: {category_key}",
        ) from error

    description = request.description.strip()
    filename = request.filename.strip()
    name = request.name.strip()

    if not description and not name:
        raise HTTPException(
            status_code=422,
            detail="Product name or description is required",
        )

    upload_path = None
    if request.upload_id:
        matches = list(UPLOADS_DIR.glob(f"{request.upload_id}.*"))
        if not matches:
            raise HTTPException(
                status_code=404,
                detail="Uploaded source file not found",
            )
        upload_path = matches[0]

    # Use a timestamp-based local identifier. The workflow store itself
    # validates that this remains a simple file name.
    product_id = datetime.now(timezone.utc).strftime(
        "product_%Y%m%d_%H%M%S_%f"
    )

    draft = {
        "name": name or description[:120],
        "category": category.key,
        "description": description or name,
        "filename": filename,
        "attributes": dict(request.attributes),
        "upload_id": request.upload_id,
        "source_file": upload_path.name if upload_path else None,
    }

    # Persist the source draft as the canonical local product JSON.
    destination = PRODUCTS_DIR / f"{product_id}_draft.json"
    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with destination.open("x", encoding="utf-8", newline="\n") as file:
            json.dump(draft, file, indent=2, ensure_ascii=False)
            file.write("\n")
    except FileExistsError as error:
        raise HTTPException(
            status_code=409,
            detail="Unable to create a unique product draft",
        ) from error

    return _build_product(destination)


@app.post("/api/products/{product_id}/ingest")
def ingest_product_source(product_id: str) -> dict[str, Any]:
    """Extract text/data from the uploaded source file for a product."""

    matches = [
        path
        for path in _draft_files()
        if _product_id(path) == product_id
    ]

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="Product draft not found",
        )

    draft_path = matches[0]

    try:
        with draft_path.open("r", encoding="utf-8") as file:
            draft = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to read product draft",
        ) from error

    upload_id = draft.get("upload_id")

    if not upload_id:
        raise HTTPException(
            status_code=422,
            detail="Product has no uploaded source file",
        )

    matches = list(UPLOADS_DIR.glob(f"{upload_id}.*"))

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="Uploaded source file not found",
        )

    source_path = matches[0]

    try:
        result = ingest_file(source_path)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail=f"Unable to ingest source file: {error}",
        ) from error

    return {
        "product_id": product_id,
        "upload_id": upload_id,
        "source_file": source_path.name,
        "ingestion": result.to_dict(),
    }


@app.post("/api/uploads", status_code=201)
async def upload_source(file: UploadFile = File(...)) -> dict[str, Any]:
    """Store a source file safely for later product-draft processing."""

    original_name = Path(file.filename or "").name

    if not original_name:
        raise HTTPException(
            status_code=422,
            detail="A file name is required",
        )

    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_UPLOAD_EXTENSIONS))
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type. Allowed: {allowed}",
        )

    content = await file.read()

    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 25 MB upload limit",
        )

    upload_id = uuid4().hex
    stored_name = f"{upload_id}{extension}"

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    destination = UPLOADS_DIR / stored_name

    try:
        destination.write_bytes(content)
    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to store uploaded file",
        ) from error

    return {
        "id": upload_id,
        "filename": original_name,
        "storedFilename": stored_name,
        "contentType": file.content_type or "application/octet-stream",
        "size": len(content),
        "status": "uploaded",
    }


@app.get("/api/products")
def products() -> dict[str, list[dict[str, Any]]]:
    result: list[dict[str, Any]] = []

    for path in _draft_files():
        try:
            result.append(_build_product(path))
        except Exception as error:
            result.append(
                {
                    "id": _product_id(path),
                    "name": path.stem,
                    "category": "unknown",
                    "status": "Error",
                    "updatedAt": "Local draft",
                    "fields": [],
                    "actionRequired": [],
                    "localIssues": [str(error)],
                }
            )

    return {"products": result}


@app.get("/api/products/{product_id}")
def product(product_id: str) -> dict[str, Any]:
    matches = [
        path
        for path in _draft_files()
        if _product_id(path) == product_id
    ]

    if not matches:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        return _build_product(matches[0])
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@app.post("/api/products/{product_id}/review/approve")
def approve_product(
    product_id: str,
    request: ApprovalRequest,
) -> dict[str, Any]:
    matches = [
        path
        for path in _draft_files()
        if _product_id(path) == product_id
    ]

    if not matches:
        raise HTTPException(status_code=404, detail="Product not found")

    path = matches[0]

    try:
        draft = load_product_draft(path)

        category_key = _category_key(draft, path)

        category = _catalog().category(category_key)
        review = build_product_review(
            draft,
            category,
            uploads_dir=UPLOADS_DIR,
        )

        confirmed = apply_approvals(
            review,
            category,
            {
                "accept": request.accept,
                "edits": request.edits,
            },
        )

        fields = []
        for field in review.fields:
            if field.attribute not in confirmed.attributes:
                continue
            approval_state = confirmed.approvals.get(field.attribute)
            fields.append(
                {
                    "attribute": field.attribute,
                    "value": confirmed.attributes[field.attribute],
                    "source": "manual" if approval_state in {"accepted", "edited"} else field.source,
                    "confidence": 1.0 if approval_state in {"accepted", "edited"} else field.confidence,
                    "review_state": approval_state or field.review_state,
                }
            )

        record = WORKFLOW_STORE.save(
            product_id,
            {
                "category": confirmed.category,
                "status": "Ready for Amazon" if confirmed.ready_for_mapping else "Review required",
                "workflow": "ready_for_amazon" if confirmed.ready_for_mapping else "review_required",
                "attributes": confirmed.attributes,
                "approvals": confirmed.approvals,
                "fields": fields,
                "actionRequired": list(confirmed.action_required),
                "localIssues": [issue["message"] for issue in confirmed.local_issues],
            },
        )
        return _approved_product(record)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@app.post("/api/products/{product_id}/variants/generate")
def generate_product_variants(
    product_id: str,
    request: VariantRequest,
) -> dict[str, Any]:
    """Generate and persist selected SKU combinations for an approved product."""
    record = WORKFLOW_STORE.load(product_id)
    if record is None:
        raise HTTPException(status_code=409, detail="Approve the product before generating variants")
    if record.get("status") != "Ready for Amazon":
        raise HTTPException(status_code=409, detail="Resolve review issues before generating variants")

    try:
        dimensions = [
            VariantDimension(
                attribute=dimension.attribute,
                options=tuple(
                    VariantOption(value=option.value, code=option.code)
                    for option in dimension.options
                ),
            )
            for dimension in request.dimensions
        ]
        variants = generate_variants(
            base_sku=request.base_sku,
            base_attributes=record["attributes"],
            dimensions=dimensions,
            excluded_combinations=request.excluded_combinations,
        )
        record["variants"] = [
            {"sku": variant.sku, "attributes": variant.attributes}
            for variant in variants
        ]
        record["workflow"] = "variants_generated"
        saved = WORKFLOW_STORE.save(product_id, record)
        return {
            "id": product_id,
            "status": saved["status"],
            "updatedAt": saved["updatedAt"],
            "variants": saved["variants"],
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/products/{product_id}/mapping")
def map_product_to_amazon(
    product_id: str,
    request: MappingRequest,
) -> dict[str, Any]:
    """Map an approved local product through an approved profile and saved schema."""
    record = WORKFLOW_STORE.load(product_id)
    if record is None:
        raise HTTPException(status_code=409, detail="Approve the product before Amazon mapping")
    if record.get("status") != "Ready for Amazon":
        raise HTTPException(status_code=409, detail="Resolve review issues before Amazon mapping")

    try:
        profile_path = _mapping_profile_path(request.profile)
        if not profile_path.exists():
            raise HTTPException(status_code=404, detail="Mapping profile not found")
        profile = load_mapping_profile(profile_path)
        if profile.local_category != record.get("category"):
            raise HTTPException(status_code=422, detail="Mapping profile does not match the product category")
        if not profile.is_approved:
            raise HTTPException(status_code=422, detail="Only an approved mapping profile may be used for an Amazon payload")
        if profile.amazon_product_type != request.product_type:
            raise HTTPException(status_code=422, detail="Mapping profile product type does not match the selected Amazon schema")

        try:
            raw_schema = load_schema(request.product_type, request.marketplace_id)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Saved Amazon schema not found") from error
        schema = parse_amazon_definition(
            raw_schema,
            product_type=request.product_type,
            marketplace_id=request.marketplace_id,
        )
        mapped = map_with_profile(record["attributes"], profile, schema)
        issues = [
            {"attribute": issue.local_attribute, "code": issue.code, "message": issue.message}
            for issue in mapped.issues
        ]
        if mapped.validation is not None:
            issues.extend(
                {"attribute": issue.field, "code": issue.code, "message": issue.message}
                for issue in mapped.validation.issues
            )
        if issues:
            raise HTTPException(status_code=422, detail={"message": "Amazon mapping failed", "issues": issues})

        record["mapping"] = {
            "profile": request.profile,
            "productType": request.product_type,
            "marketplaceId": request.marketplace_id,
            "attributes": mapped.attributes,
        }
        record["workflow"] = "amazon_mapped"
        saved = WORKFLOW_STORE.save(product_id, record)
        return {
            "id": product_id,
            "status": saved["status"],
            "updatedAt": saved["updatedAt"],
            "mapping": saved["mapping"],
        }
    except HTTPException:
        raise
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/products/{product_id}/validate")
def validate_product_mapping(product_id: str) -> dict[str, Any]:
    """Validate persisted mapped attributes before any listing preview or submission."""
    record = WORKFLOW_STORE.load(product_id)
    if record is None:
        raise HTTPException(status_code=409, detail="Approve the product before validation")
    mapping = record.get("mapping")
    if not isinstance(mapping, dict):
        raise HTTPException(status_code=409, detail="Map the product to an Amazon schema before validation")

    product_type = mapping.get("productType")
    marketplace_id = mapping.get("marketplaceId")
    attributes = mapping.get("attributes")
    if not isinstance(product_type, str) or not isinstance(marketplace_id, str) or not isinstance(attributes, dict):
        raise HTTPException(status_code=500, detail="Stored mapping record is invalid")

    try:
        raw_schema = load_schema(product_type, marketplace_id)
        schema = parse_amazon_definition(
            raw_schema,
            product_type=product_type,
            marketplace_id=marketplace_id,
        )
        report = validate_attributes(attributes, schema)
        validation = {
            "valid": report.is_valid,
            "issues": [
                {"field": issue.field, "code": issue.code, "message": issue.message}
                for issue in report.issues
            ],
        }
        record["validation"] = validation
        record["workflow"] = "validated" if report.is_valid else "validation_failed"
        saved = WORKFLOW_STORE.save(product_id, record)
        return {
            "id": product_id,
            "updatedAt": saved["updatedAt"],
            **validation,
        }
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Saved Amazon schema not found") from error
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/products/{product_id}/preview")
def preview_listing_payload(
    product_id: str,
    request: PreviewRequest,
) -> dict[str, Any]:
    """Build and persist a reviewable Listings Items payload without submitting it."""
    record = WORKFLOW_STORE.load(product_id)
    if record is None:
        raise HTTPException(status_code=409, detail="Approve the product before creating a preview")
    mapping = record.get("mapping")
    if not isinstance(mapping, dict):
        raise HTTPException(status_code=409, detail="Map the product to an Amazon schema before creating a preview")

    product_type = mapping.get("productType")
    marketplace_id = mapping.get("marketplaceId")
    attributes = mapping.get("attributes")
    if not isinstance(product_type, str) or not isinstance(marketplace_id, str) or not isinstance(attributes, dict):
        raise HTTPException(status_code=500, detail="Stored mapping record is invalid")

    try:
        raw_schema = load_schema(product_type, marketplace_id)
        schema = parse_amazon_definition(
            raw_schema,
            product_type=product_type,
            marketplace_id=marketplace_id,
        )
        payload, report = build_listing_payload(
            sku=request.sku,
            product_type=product_type,
            attributes=attributes,
            schema=schema,
            requirements=request.requirements,
        )
        validation = {
            "valid": report.is_valid,
            "issues": [
                {"field": issue.field, "code": issue.code, "message": issue.message}
                for issue in report.issues
            ],
        }
        preview = {"payload": payload, **validation}
        record["preview"] = preview
        record["workflow"] = "preview_ready" if report.is_valid else "preview_blocked"
        saved = WORKFLOW_STORE.save(product_id, record)
        return {"id": product_id, "updatedAt": saved["updatedAt"], **preview}
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Saved Amazon schema not found") from error
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/products/{product_id}/submit")
def submit_product_listing(
    product_id: str,
    request: SubmissionRequest,
) -> dict[str, Any]:
    """Submit only a freshly validated preview to the explicitly selected sandbox."""
    if request.environment.lower() != "sandbox":
        raise HTTPException(
            status_code=403,
            detail="Production submission is disabled until production authorization and credentials are configured",
        )
    if os.getenv("AWS_ENV", "").upper() != "SANDBOX":
        raise HTTPException(status_code=409, detail="Set AWS_ENV=SANDBOX for a sandbox submission")

    record = WORKFLOW_STORE.load(product_id)
    if record is None:
        raise HTTPException(status_code=409, detail="Approve the product before submission")
    mapping = record.get("mapping")
    if not isinstance(mapping, dict):
        raise HTTPException(status_code=409, detail="Map the product before submission")
    product_type = mapping.get("productType")
    marketplace_id = mapping.get("marketplaceId")
    attributes = mapping.get("attributes")
    if not isinstance(product_type, str) or not isinstance(marketplace_id, str) or not isinstance(attributes, dict):
        raise HTTPException(status_code=500, detail="Stored mapping record is invalid")

    try:
        raw_schema = load_schema(product_type, marketplace_id)
        schema = parse_amazon_definition(raw_schema, product_type=product_type, marketplace_id=marketplace_id)
        payload, report = build_listing_payload(
            sku=request.sku,
            product_type=product_type,
            attributes=attributes,
            schema=schema,
            requirements=request.requirements,
        )
        if not report.is_valid:
            issues = [
                {"field": issue.field, "code": issue.code, "message": issue.message}
                for issue in report.issues
            ]
            record["submission"] = {"status": "blocked", "environment": "sandbox", "issues": issues}
            WORKFLOW_STORE.save(product_id, record)
            raise HTTPException(status_code=422, detail={"message": "Submission blocked by validation", "issues": issues})

        response = get_listings_client().put_listings_item(
            sellerId=request.seller_id,
            sku=request.sku,
            marketplaceIds=[marketplace_id],
            body={key: value for key, value in payload.items() if key != "sku"},
        )
        response_payload = getattr(response, "payload", response)
        record["submission"] = {
            "status": "submitted_to_sandbox",
            "environment": "sandbox",
            "sku": request.sku,
            "response": response_payload if isinstance(response_payload, (dict, list, str, int, float, bool, type(None))) else str(response_payload),
        }
        record["workflow"] = "submitted_to_sandbox"
        saved = WORKFLOW_STORE.save(product_id, record)
        return {"id": product_id, "updatedAt": saved["updatedAt"], "submission": saved["submission"]}
    except HTTPException:
        raise
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Saved Amazon schema not found") from error
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
