"""Resolve the JSON-schema link returned by Amazon Product Type Definitions."""

from typing import Any
from urllib.parse import urlparse

import httpx


def schema_url_from_definition(definition: dict[str, Any]) -> str:
    """Return the HTTPS schema URL from an SP-API definition envelope."""
    schema = definition.get("schema")
    if not isinstance(schema, dict):
        raise ValueError("Definition does not include a schema descriptor")

    link = schema.get("link")
    if not isinstance(link, dict):
        raise ValueError("Definition schema does not include a download link")

    resource = link.get("resource")
    if not isinstance(resource, str):
        raise ValueError("Definition schema link does not include a resource URL")

    parsed = urlparse(resource)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Amazon schema URL must use HTTPS")

    # Amazon Sandbox may return this placeholder rather than a downloadable URL.
    if parsed.netloc == "schema-url":
        raise RuntimeError(
            "Sandbox returned a schema placeholder, so field constraints are unavailable. "
            "Use a real Sandbox definition URL or the production API to download it."
        )

    return resource


def download_schema(definition: dict[str, Any], *, timeout_seconds: float = 30.0) -> dict[str, Any]:
    """Download and validate the JSON schema linked from a definition envelope."""
    url = schema_url_from_definition(definition)
    response = httpx.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Downloaded Amazon schema is not a JSON object")
    return payload
