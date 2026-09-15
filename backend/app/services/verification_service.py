"""
Document Verification and Forensic Orchestration Service.
Extracts Page 1 & Page 2, recomputes canonical SHA-256 digest, decodes QR code,
and executes constant-time cryptographic comparison.
"""
from datetime import datetime, timezone
import hmac
import fitz  # PyMuPDF
from app.services.hash_service import compute_canonical_page_hash
from app.services.qr_service import decode_qr_from_page, extract_hash_from_qr_payload


def verify_secured_pdf(pdf_bytes: bytes, filename: str) -> dict:
    """
    Performs end-to-end verification of an uploaded secured PDF document.

    Args:
        pdf_bytes (bytes): Binary data of the PDF.
        filename (str): Uploaded filename.

    Returns:
        dict: Complete verification report containing status verdict, hashes, and telemetry.
    """
    verification_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        return {
            "file_name": filename,
            "is_authentic": False,
            "status_text": "INVALID",
            "original_hash": None,
            "calculated_hash": None,
            "verification_timestamp": verification_time,
            "page_count": 0,
            "details": f"Corrupted or non-PDF file: {str(e)}",
        }

    page_count = doc.page_count

    # Step 1: Validate minimum page count of 2
    if page_count < 2:
        doc.close()
        return {
            "file_name": filename,
            "is_authentic": False,
            "status_text": "INVALID",
            "original_hash": None,
            "calculated_hash": None,
            "verification_timestamp": verification_time,
            "page_count": page_count,
            "details": "Invalid document: A verified secured document must contain at least 2 pages (Protected Page + Authentication QR Page).",
        }

    # Step 2 & 3: Extract Page 1 and recalculate canonical SHA-256 hash
    page_1 = doc[0]
    calculated_hash = compute_canonical_page_hash(page_1).lower()

    # Step 4 & 5: Extract Page 2 and decode QR code
    page_2 = doc[1]
    try:
        qr_payload = decode_qr_from_page(page_2)
        original_hash = extract_hash_from_qr_payload(qr_payload).lower()
        from app.services.qr_service import extract_document_id_from_qr_payload
        document_id = extract_document_id_from_qr_payload(qr_payload)
    except Exception as e:
        doc.close()
        return {
            "file_name": filename,
            "is_authentic": False,
            "status_text": "INVALID",
            "original_hash": None,
            "calculated_hash": calculated_hash,
            "verification_timestamp": verification_time,
            "page_count": page_count,
            "details": f"Failed to detect or decode QR code on Page 2: {str(e)}",
            "document_id": None,
        }

    doc.close()

    # Step 6 & 7: Cryptographic comparison (constant-time)
    hashes_match = hmac.compare_digest(original_hash, calculated_hash)

    if hashes_match:
        status_text = "AUTHENTIC"
        details = "Page 1 cryptographic hash matches QR code payload exactly. Document integrity verified."
    else:
        status_text = "MODIFIED"
        details = "Cryptographic mismatch: The rendered visual presentation of Page 1 has been altered after sealing."

    return {
        "file_name": filename,
        "is_authentic": hashes_match,
        "status_text": status_text,
        "original_hash": original_hash,
        "calculated_hash": calculated_hash,
        "verification_timestamp": verification_time,
        "page_count": page_count,
        "details": details,
        "document_id": document_id,
        "qr_payload": qr_payload,
    }
