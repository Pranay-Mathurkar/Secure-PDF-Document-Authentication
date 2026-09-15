"""Phase 10 API integration tests."""
import fitz
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.services.hash_service import compute_canonical_page_hash
from app.services.qr_service import generate_qr_image_bytes
from app.services.pdf_service import assemble_secured_pdf


client = TestClient(app)


def _original_pdf() -> bytes:
    document = fitz.open()
    page = document.new_page(width=200, height=120)
    page.insert_text(fitz.Point(20, 45), "Original document", fontsize=16)
    result = document.tobytes()
    document.close()
    return result


def _secured_pdf(original: bytes) -> bytes:
    source = fitz.open(stream=original, filetype="pdf")
    digest = compute_canonical_page_hash(source[0])
    source.close()
    return assemble_secured_pdf(
        original,
        digest,
        "2026-09-13 00:00:00 UTC",
        generate_qr_image_bytes(digest),
    )


def test_existing_verification_endpoint_works_without_original_file():
    original = _original_pdf()
    response = client.post(
        "/api/v1/verify/verify-pdf",
        files={"file": ("secured.pdf", _secured_pdf(original), "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_authentic"] is True
    assert payload["hash"] is None
    assert payload["dsp_analysis_available"] is False


def test_verification_endpoint_returns_dsp_report_and_visual_urls():
    original = _original_pdf()
    response = client.post(
        "/api/v1/verify/verify-pdf",
        files={
            "file": ("secured.pdf", _secured_pdf(original), "application/pdf"),
            "original_file": ("original.pdf", original, "application/pdf"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dsp_analysis_available"] is True
    assert payload["authentication"]["status"] == "AUTHENTIC"
    assert payload["hash"]["status"] == "MATCH"
    assert payload["similarity"]["ssim"] > 0.99
    assert payload["frequency_analysis"]["fft_similarity"] == 100.0
    assert payload["edge_analysis"]["edge_similarity"] == 100.0
    assert len(payload["visual_results"]["pages"]) == 1
    assert "fft_spectrum_url" in payload["visual_results"]["pages"][0]
    artifact_url = payload["visual_results"]["pages"][0]["difference_image_url"]
    artifact_response = client.get(artifact_url)
    assert artifact_response.status_code == 200
    assert artifact_response.headers["content-type"] == "image/png"


def test_invalid_pdf_returns_meaningful_client_error():
    response = client.post(
        "/api/v1/verify/verify-pdf",
        files={"file": ("invalid.pdf", b"not a pdf", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["is_authentic"] is False
