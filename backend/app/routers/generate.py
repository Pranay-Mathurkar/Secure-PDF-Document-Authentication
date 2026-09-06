"""
Document Generation Router.
Handles PDF uploading, deterministic canonical hashing, QR code creation, and secured PDF downloading.
"""
from datetime import datetime, timezone
from pathlib import Path
import re
import fitz
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

from app.config import settings
from app.services.hash_service import compute_canonical_page_hash
from app.services.qr_service import generate_qr_image_bytes
from app.services.pdf_service import assemble_secured_pdf
from app.schemas.response_models import DocumentGenerationResponse
from app.utils.file_utils import validate_pdf_file

router = APIRouter(prefix="/generate", tags=["Document Generation"])


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename to prevent directory traversal and special character issues."""
    base = Path(filename).stem
    clean_base = re.sub(r"[^a-zA-Z0-9_\-]", "_", base)[:50]
    return f"{clean_base}_secured.pdf"


@router.post(
    "/secure-pdf",
    response_model=DocumentGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a secured 2-page authenticated PDF"
)
async def generate_secured_pdf(file: UploadFile = File(...)):
    """
    Ingests an original PDF document, computes the canonical SHA-256 hash of Page 1,
    synthesizes a QR code authentication certificate page, merges them into a 2-page
    tamper-evident PDF, and provides a download endpoint.
    """
    validate_pdf_file(file, settings.MAX_FILE_SIZE_MB * 1024 * 1024)

    pdf_bytes = await file.read()

    # Verify PDF validity via PyMuPDF
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if doc.page_count < 1:
            raise ValueError("PDF has no pages.")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded file is corrupted or not a valid PDF document: {str(e)}"
        )

    # 1. Extract Page 1 and compute deterministic canonical hash
    try:
        first_page = doc[0]
        sha256_hash = compute_canonical_page_hash(first_page)
    except Exception as e:
        doc.close()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate canonical hash: {str(e)}"
        )
    finally:
        doc.close()

    # 2. Timestamp
    now_utc = datetime.now(timezone.utc)
    timestamp_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    timestamp_iso = now_utc.isoformat()

    # 3. Generate QR code PNG
    qr_png_bytes = generate_qr_image_bytes(sha256_hash)

    # 4. Assemble 2-page secured PDF
    try:
        secured_pdf_bytes = assemble_secured_pdf(
            original_pdf_bytes=pdf_bytes,
            sha256_hash=sha256_hash,
            timestamp_str=timestamp_str,
            qr_png_bytes=qr_png_bytes,
            algorithm=settings.HASH_ALGORITHM,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compile secured PDF: {str(e)}"
        )

    # 5. Persist to storage outputs
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_filename = f"{int(now_utc.timestamp())}_{sanitize_filename(file.filename)}"
    out_filepath = settings.OUTPUT_DIR / out_filename

    with open(out_filepath, "wb") as f:
        f.write(secured_pdf_bytes)

    download_url = f"{settings.API_PREFIX}/generate/download/{out_filename}"

    return DocumentGenerationResponse(
        success=True,
        message="Secured 2-page PDF created successfully.",
        file_name=out_filename,
        sha256_hash=sha256_hash,
        algorithm=settings.HASH_ALGORITHM,
        timestamp=timestamp_iso,
        download_url=download_url,
    )


@router.get(
    "/download/{file_name}",
    response_class=FileResponse,
    summary="Download a previously generated secured PDF"
)
async def download_secured_pdf(file_name: str):
    """Safely streams the generated 2-page secured PDF file."""
    # Prevent path traversal
    safe_name = Path(file_name).name
    file_path = settings.OUTPUT_DIR / safe_name

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="The requested secured PDF was not found or has expired."
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=safe_name,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'}
    )
