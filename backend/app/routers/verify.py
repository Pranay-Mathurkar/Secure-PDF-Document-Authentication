"""
Document Verification Router.
Handles uploading a 2-page secured PDF, extracting the QR code, recalculating the
Page 1 canonical hash, and returning forensic comparison results.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.config import settings
from app.services.verification_service import verify_secured_pdf
from app.schemas.response_models import DocumentVerificationResponse
from app.utils.file_utils import validate_pdf_file

router = APIRouter(prefix="/verify", tags=["Document Verification"])


@router.post(
    "/verify-pdf",
    response_model=DocumentVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify the authenticity of a secured 2-page PDF"
)
async def verify_document(file: UploadFile = File(...)):
    """
    Ingests a secured 2-page PDF, decodes the QR code from Page 2 to retrieve
    the stored SHA-256 digest, renders Page 1 at the fixed canonical resolution to
    recompute the digest, and performs constant-time cryptographic verification.
    """
    validate_pdf_file(file, settings.MAX_FILE_SIZE_MB * 1024 * 1024)

    pdf_bytes = await file.read()

    result = verify_secured_pdf(pdf_bytes=pdf_bytes, filename=file.filename)

    return DocumentVerificationResponse(
        success=True,
        file_name=result["file_name"],
        is_authentic=result["is_authentic"],
        status_text=result["status_text"],
        original_hash=result["original_hash"],
        calculated_hash=result["calculated_hash"],
        algorithm=settings.HASH_ALGORITHM,
        verification_timestamp=result["verification_timestamp"],
        page_count=result["page_count"],
        details=result["details"],
    )
