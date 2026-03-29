from __future__ import annotations

import re
from pathlib import Path

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.ingestion.normalization import SUPPORTED_INPUT_FORMATS

SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_upload_filename(filename: str | None, *, slug: str) -> str:
    original = Path(filename or f"{slug}-import").name.strip()
    cleaned = SAFE_FILENAME_PATTERN.sub("-", original).strip(".-")
    return cleaned or f"{slug}-import"


def validate_upload_payload(slug: str, *, filename: str | None, raw_bytes: bytes) -> tuple[str, str]:
    settings = get_settings()
    safe_filename = sanitize_upload_filename(filename, slug=slug)
    suffix = Path(safe_filename).suffix.lower().lstrip(".")
    allowed_formats = SUPPORTED_INPUT_FORMATS.get(slug, ["json"])

    if not raw_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file was empty")
    if len(raw_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeded the {settings.max_upload_size_bytes // (1024 * 1024)} MB limit",
        )
    if suffix not in allowed_formats:
        allowed = ", ".join(f".{item}" for item in allowed_formats)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type for {slug}. Allowed formats: {allowed}",
        )

    return safe_filename, suffix
