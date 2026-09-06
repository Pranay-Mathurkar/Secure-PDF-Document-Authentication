"""
File validation and management utility functions.
"""
from pathlib import Path
from fastapi import UploadFile, HTTPException


def validate_pdf_file(file: UploadFile, max_size_bytes: int) -> None:
    """Validate file extension and content type for PDF uploads."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only PDF files are supported."
        )
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid content-type header. Expected 'application/pdf'."
        )


def ensure_directory_exists(directory_path: Path) -> Path:
    """Ensure that the given directory path exists."""
    directory_path.mkdir(parents=True, exist_ok=True)
    return directory_path
