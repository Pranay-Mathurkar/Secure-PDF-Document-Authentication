"""
Deterministic Canonical Hashing Service.
Renders a PDF page to a standardized raw RGB pixel buffer at fixed DPI
to compute an invariant cryptographic SHA-256 digest.
"""
import hashlib
import fitz  # PyMuPDF
from app.config import settings


def compute_canonical_page_hash(page: fitz.Page, dpi: int = None) -> str:
    """
    Renders the page at a fixed DPI in standard RGB colorspace without alpha channel,
    extracts the raw uncompressed pixel buffer, and returns its SHA-256 hexadecimal digest.

    Args:
        page (fitz.Page): The PyMuPDF page object to hash.
        dpi (int, optional): The resolution to render at. Defaults to settings.CANONICAL_DPI (150).

    Returns:
        str: 64-character lowercase hexadecimal SHA-256 hash.
    """
    if dpi is None:
        dpi = settings.CANONICAL_DPI

    # Standard PDF points are 72 per inch. Calculate zoom matrix.
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    # Render pixmap: RGB colorspace, alpha=False (no transparency channel variance)
    pixmap = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False)

    # Extract raw pixel bytes
    pixel_bytes = pixmap.samples

    # Compute SHA-256 digest
    hasher = hashlib.sha256()
    hasher.update(pixel_bytes)
    return hasher.hexdigest()
