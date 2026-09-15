"""Persistent cryptographic records independent of DSP processing."""
import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import fitz

from app.config import settings
from app.services.hash_service import compute_canonical_page_hash


def compute_file_sha256(pdf_bytes: bytes) -> str:
    """Hash the supplied PDF bytes without invoking any image/DSP code."""
    return hashlib.sha256(pdf_bytes).hexdigest()


def create_hash_record(
    pdf_bytes: bytes,
    page: fitz.Page,
    document_id: str | None = None,
) -> dict:
    """Create and persist a cryptographic record for a source document."""
    record = {
        "document_id": document_id or uuid4().hex,
        "algorithm": "SHA-256",
        "file_sha256": compute_file_sha256(pdf_bytes),
        "canonical_page1_sha256": compute_canonical_page_hash(page),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    settings.HASH_RECORD_DIR.mkdir(parents=True, exist_ok=True)
    path = settings.HASH_RECORD_DIR / f"{record['document_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def load_hash_record(document_id: str) -> dict:
    """Load a hash record by document ID."""
    path = settings.HASH_RECORD_DIR / f"{Path(document_id).name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Hash record not found for document ID: {document_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def compare_canonical_page_hash(
    page: fitz.Page,
    record: dict,
) -> dict:
    """Compare candidate canonical Page 1 pixels with a stored hash record."""
    calculated = compute_canonical_page_hash(page).lower()
    expected = str(record["canonical_page1_sha256"]).lower()
    matched = hmac.compare_digest(expected, calculated)
    return {
        "status": "MATCH" if matched else "MISMATCH",
        "match": matched,
        "expected": expected,
        "calculated": calculated,
        "file_sha256": record.get("file_sha256"),
        "document_id": record.get("document_id"),
    }


def finalize_hash_record(record: dict, secured_pdf_bytes: bytes) -> dict:
    """Add the exact secured-file digest after the QR-bearing PDF is assembled."""
    finalized = dict(record)
    finalized["secured_file_sha256"] = compute_file_sha256(secured_pdf_bytes)
    path = settings.HASH_RECORD_DIR / f"{Path(record['document_id']).name}.json"
    path.write_text(json.dumps(finalized, indent=2), encoding="utf-8")
    return finalized


def compare_secured_file_hash(pdf_bytes: bytes, record: dict) -> dict:
    """Compare candidate secured PDF bytes without importing any DSP module."""
    calculated = compute_file_sha256(pdf_bytes)
    expected = record.get("secured_file_sha256")
    matched = bool(expected) and hmac.compare_digest(str(expected).lower(), calculated)
    return {
        "status": "MATCH" if matched else "MISMATCH",
        "match": matched,
        "expected": expected,
        "calculated": calculated,
        "document_id": record.get("document_id"),
    }
