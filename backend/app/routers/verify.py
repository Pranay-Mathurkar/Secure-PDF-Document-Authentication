"""Document verification and optional multi-layer DSP analysis."""
from pathlib import Path
from uuid import uuid4

import cv2
import fitz
from fastapi import APIRouter, UploadFile, File, HTTPException, status

from app.config import settings
from app.schemas.response_models import DocumentVerificationResponse
from app.services.authentication_service import authenticate_documents
from app.services.dsp_analysis_service import analyze_dsp_pages
from app.services.dsp_reference_service import load_reference_page
from app.services.hash_record_service import (
    compare_canonical_page_hash,
    compare_secured_file_hash,
    load_hash_record,
)
from app.services.feature_service import calculate_canny_edges
from app.services.fft_service import generate_magnitude_spectrum_image
from app.services.preprocessing_service import DSPProcessingError, preprocess_pdf_pages
from app.services.preprocessing_service import render_page_to_image
from app.services.tamper_detection_service import localize_tampering
from app.services.verification_service import verify_secured_pdf
from app.utils.file_utils import validate_pdf_file


router = APIRouter(prefix="/verify", tags=["Document Verification"])


def _validate_and_read_pdf(file: UploadFile, content: bytes) -> bytes:
    validate_pdf_file(file, settings.MAX_FILE_SIZE_MB * 1024 * 1024)
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Uploaded PDF exceeds the maximum file size.")
    return content


def _write_visual(image, directory: Path, filename: str) -> str:
    path = directory / filename
    if not cv2.imwrite(str(path), image):
        raise DSPProcessingError(f"Failed to write visual analysis artifact: {filename}")
    relative_directory = directory.relative_to(settings.OUTPUT_DIR).as_posix()
    return f"{settings.API_PREFIX}/visual-results/{relative_directory}/{filename}"


def _write_forensic_visual(image, directory: Path, filename: str) -> str:
    path = directory / filename
    if not cv2.imwrite(str(path), image):
        raise DSPProcessingError(f"Failed to write forensic artifact: {filename}")
    relative_path = path.relative_to(settings.FORENSIC_RESULTS_DIR).as_posix()
    return f"{settings.API_PREFIX}/forensic-results/{relative_path}"


def _persistent_dsp_report(pdf_bytes: bytes, document_id: str) -> dict:
    reference = load_reference_page(document_id)
    candidate_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if candidate_document.page_count == 0:
            raise DSPProcessingError("Candidate document has no renderable pages.")
        candidate_page = render_page_to_image(
            candidate_document[0],
            dpi=settings.CANONICAL_DPI,
        )
    finally:
        candidate_document.close()

    if candidate_page is None:
        raise DSPProcessingError("Candidate document has no renderable pages.")
    analysis = analyze_dsp_pages([reference], [candidate_page])
    analysis["document_id"] = document_id
    analysis["reference_source"] = "persistent_canonical_page1"
    analysis["candidate_source"] = "uploaded_pdf_page1"
    directory = settings.FORENSIC_RESULTS_DIR / Path(document_id).name
    directory.mkdir(parents=True, exist_ok=True)
    localization = localize_tampering(reference, candidate_page)
    visual = {
        key: _write_forensic_visual(image, directory, f"page_1_{key}.png")
        for key, image in localization["outputs"].items()
    }
    fft_url = _write_forensic_visual(
        generate_magnitude_spectrum_image(
            preprocess_pdf_pages(pdf_bytes, page_indices=[0])[0],
            preprocess=False,
        ),
        directory,
        "page_1_fft_spectrum.png",
    )
    analysis["visual_results"] = {"pages": [{
        "page": 1,
        "original_image_url": _write_forensic_visual(reference, directory, "page_1_original.png"),
        "preprocessed_image_url": _write_forensic_visual(
            preprocess_pdf_pages(pdf_bytes, page_indices=[0])[0],
            directory,
            "page_1_candidate_preprocessed.png",
        ),
        "edge_map_url": _write_forensic_visual(
            calculate_canny_edges(candidate_page),
            directory,
            "page_1_edge_map.png",
        ),
        "fft_spectrum_url": fft_url,
        "difference_image_url": visual["difference_image"],
        "tampering_mask_url": visual["tampering_mask"],
        "heatmap_url": visual["tampering_heatmap"],
        "bounding_box_url": visual["bounding_box_image"],
    }]}
    return analysis


def _build_dsp_report(
    secured_pdf: bytes,
    original_pdf: bytes,
    authentication: dict,
) -> dict:
    original_pages = preprocess_pdf_pages(original_pdf)
    secured_pages = preprocess_pdf_pages(secured_pdf)
    if len(secured_pages) > len(original_pages):
        secured_pages = secured_pages[:len(original_pages)]
    if len(original_pages) != len(secured_pages):
        raise DSPProcessingError(
            "Original and verification documents must contain the same number of comparable pages."
        )

    artifact_directory = settings.OUTPUT_DIR / "analysis" / uuid4().hex
    artifact_directory.mkdir(parents=True, exist_ok=True)
    visual_pages = []
    for page_number, (original, verification) in enumerate(
        zip(original_pages, secured_pages), start=1
    ):
        localization = localize_tampering(
            original,
            verification,
            output_dir=artifact_directory,
            page_number=page_number,
        )
        spectrum_path = _write_visual(
            generate_magnitude_spectrum_image(verification, preprocess=False),
            artifact_directory,
            f"page_{page_number}_fft_spectrum.png",
        )
        visual_pages.append({
            "page": page_number,
            "original_image_url": _write_visual(
                original,
                artifact_directory,
                f"page_{page_number}_original_image.png",
            ),
            "preprocessed_image_url": _write_visual(
                original,
                artifact_directory,
                f"page_{page_number}_preprocessed_image.png",
            ),
            "edge_map_url": _write_visual(
                calculate_canny_edges(original, preprocess=False),
                artifact_directory,
                f"page_{page_number}_edge_map.png",
            ),
            "fft_spectrum_url": spectrum_path,
            "difference_image_url": _write_visual(
                localization["outputs"]["difference_image"],
                artifact_directory,
                f"page_{page_number}_difference_image.png",
            ),
            "tampering_mask_url": _write_visual(
                localization["outputs"]["tampering_mask"],
                artifact_directory,
                f"page_{page_number}_tampering_mask.png",
            ),
            "heatmap_url": _write_visual(
                localization["outputs"]["tampering_heatmap"],
                artifact_directory,
                f"page_{page_number}_tampering_heatmap.png",
            ),
            "bounding_box_url": _write_visual(
                localization["outputs"]["bounding_box_image"],
                artifact_directory,
                f"page_{page_number}_bounding_box_image.png",
            ),
        })

    report = dict(authentication)
    report["visual_results"] = {"pages": visual_pages}
    return report


@router.post(
    "/verify-pdf",
    response_model=DocumentVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify a secured PDF and optionally run DSP authentication analysis",
)
async def verify_document(
    file: UploadFile = File(...),
    original_file: UploadFile | None = File(
        default=None,
        description="Optional original PDF used as the DSP comparison baseline.",
    ),
):
    """
    Run unchanged SHA-256/QR verification. When original_file is provided,
    additionally return SSIM/MSE/PSNR, FFT, DCT, edge, tampering, confidence,
    page-level results, and visual artifact URLs.
    """
    pdf_bytes = _validate_and_read_pdf(file, await file.read())
    original_bytes = None
    if original_file is not None:
        original_bytes = _validate_and_read_pdf(original_file, await original_file.read())

    result = verify_secured_pdf(pdf_bytes=pdf_bytes, filename=file.filename)
    response = {
        "success": True,
        "file_name": result["file_name"],
        "is_authentic": result["is_authentic"],
        "status_text": result["status_text"],
        "original_hash": result["original_hash"],
        "calculated_hash": result["calculated_hash"],
        "algorithm": settings.HASH_ALGORITHM,
        "verification_timestamp": result["verification_timestamp"],
        "page_count": result["page_count"],
        "details": result["details"],
        "message": "SHA-256 and QR verification completed.",
        "dsp_analysis_available": False,
        "hash_analysis": {
            "status": "MATCH" if result["is_authentic"] else "MISMATCH",
            "document_id": result.get("document_id"),
            "expected_canonical_page1_sha256": result["original_hash"],
            "calculated_canonical_page1_sha256": result["calculated_hash"],
        },
    }

    document_id = result.get("document_id")
    if document_id:
        try:
            record = load_hash_record(document_id)
            document = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_hash_result = compare_canonical_page_hash(document[0], record)
            document.close()
            hash_result = compare_secured_file_hash(pdf_bytes, record)
            hash_result["canonical_page1"] = page_hash_result
            response["hash_analysis"] = hash_result
            response["original_hash"] = page_hash_result["expected"]
            response["calculated_hash"] = page_hash_result["calculated"]
            response["is_authentic"] = hash_result["match"] and page_hash_result["match"]
        except FileNotFoundError:
            response["hash_analysis"]["status"] = "LEGACY_RECORD_UNAVAILABLE"

    # A persisted document ID is authoritative for DSP. Even when the legacy
    # original_file field is supplied, compare the candidate against the
    # canonical reference associated with the QR document ID.
    if document_id:
        try:
            dsp = _persistent_dsp_report(pdf_bytes, document_id)
        except FileNotFoundError:
            response["message"] = (
                "Hash verification completed. DSP reference is unavailable for this document."
            )
            response["dsp_analysis"] = {
                "available": False,
                "reason": "DSP reference page not found for document ID.",
                "document_id": document_id,
            }
            return DocumentVerificationResponse(**response)
        except DSPProcessingError as exc:
            raise HTTPException(status_code=422, detail=f"DSP analysis failed: {exc}") from exc
        response["dsp_analysis"] = dsp
        response["dsp_analysis_available"] = True
        response["authentication"] = {
            "status": "AUTHENTIC" if response["is_authentic"] and not dsp["tampering_detected"] else "MODIFIED",
            "confidence": float(
                0.4 * (100.0 if response["is_authentic"] else 0.0)
                + 0.25 * dsp["ssim"] * 100.0
                + 0.15 * dsp["fft_similarity"]
                + 0.10 * dsp["dct_similarity"]
                + 0.10 * dsp["edge_similarity"]
            ),
        }
        response["similarity"] = {
            "ssim": dsp["ssim"],
            "mse": dsp["mse"],
            "psnr": dsp["psnr"],
        }
        response["frequency_analysis"] = {
            "fft_similarity": dsp["fft_similarity"],
            "dct_similarity": dsp["dct_similarity"],
        }
        response["edge_analysis"] = {"edge_similarity": dsp["edge_similarity"]}
        response["tampering"] = {
            "detected": dsp["tampering_detected"],
            "percentage": dsp["tampering_percentage"],
            "modified_regions": dsp["modified_regions"],
            "modified_pages": dsp["modified_pages"],
        }
        response["pages"] = dsp["pages"]
        response["visual_results"] = dsp["visual_results"]
        response["message"] = "Independent hash and DSP analyses completed."
        return DocumentVerificationResponse(**response)

    if original_bytes is None:
        response["dsp_analysis"] = {
            "available": False,
            "reason": "No document_id was present in the QR payload; this is a legacy document.",
        }
        response["message"] += (
            " DSP reference analysis is unavailable because the QR payload has no document_id."
        )
        return DocumentVerificationResponse(**response)

    if not result["original_hash"] or not result["calculated_hash"]:
        raise HTTPException(
            status_code=422,
            detail="DSP analysis requires a valid secured document with a decodable original hash.",
        )
    try:
        original_pages = preprocess_pdf_pages(original_bytes)
        secured_pages = preprocess_pdf_pages(pdf_bytes)
        comparable_secured_pages = secured_pages[:len(original_pages)]
        authentication = authenticate_documents(
            original_pages,
            comparable_secured_pages,
            result["original_hash"],
            result["calculated_hash"],
        )
        authentication = _build_dsp_report(pdf_bytes, original_bytes, authentication)
    except DSPProcessingError as exc:
        raise HTTPException(status_code=422, detail=f"DSP analysis failed: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate DSP analysis: {exc}") from exc

    response.update({
        "message": "SHA-256, QR, and DSP authentication analysis completed.",
        "dsp_analysis_available": True,
        "authentication": {
            "status": authentication["status"],
            "confidence": authentication["confidence_score"],
            "visual_confidence": authentication["visual_confidence_score"],
        },
        "hash": authentication["hash"],
        "similarity": authentication["similarity"],
        "frequency_analysis": authentication["frequency"],
        "edge_analysis": authentication["edge"],
        "tampering": {
            "detected": authentication["tampering"]["detected"],
            "percentage": authentication["tampering"]["tampering_percentage"],
            "modified_regions": authentication["tampering"]["total_region_count"],
            "modified_pages": authentication["tampering"]["modified_pages"],
        },
        "pages": authentication["pages"],
        "visual_results": authentication["visual_results"],
    })
    return DocumentVerificationResponse(**response)
