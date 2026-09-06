"""
QR Code Generation and Computer Vision Decoding Service.
Encodes SHA-256 digests with Level H error correction and decodes from PDF pages via OpenCV.
"""
import io
import json
import numpy as np
import cv2
import fitz  # PyMuPDF
from PIL import Image
import qrcode
from qrcode.constants import ERROR_CORRECT_H


def generate_qr_image_bytes(payload: str) -> bytes:
    """
    Generates a high-contrast QR code image as PNG bytes using Error Correction Level H.

    Args:
        payload (str): The string data to encode (the SHA-256 hash or JSON metadata).

    Returns:
        bytes: PNG-encoded image bytes.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def decode_qr_from_page(page: fitz.Page, dpi: int = 200) -> str:
    """
    Renders a PDF page to an image and detects/decodes embedded QR codes using OpenCV.

    Args:
        page (fitz.Page): The PyMuPDF page (typically Page 2 of the secured document).
        dpi (int): Rendering resolution for barcode detection.

    Returns:
        str: Decoded string payload from the QR code.

    Raises:
        ValueError: If no valid QR code could be detected and decoded.
    """
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False)

    # Convert PyMuPDF pixmap buffer to OpenCV BGR numpy array
    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    detector = cv2.QRCodeDetector()

    # Pass 1: Direct detection on color image
    decoded_text, points, _ = detector.detectAndDecode(img_bgr)
    if decoded_text and decoded_text.strip():
        return decoded_text.strip()

    # Pass 2: Grayscale with Otsu thresholding for enhanced contrast
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    decoded_text, points, _ = detector.detectAndDecode(thresh)
    if decoded_text and decoded_text.strip():
        return decoded_text.strip()

    # Pass 3: Higher resolution retry if needed
    if dpi < 300:
        return decode_qr_from_page(page, dpi=300)

    raise ValueError("No readable QR code was detected on the authentication page.")


def extract_hash_from_qr_payload(payload: str) -> str:
    """
    Extracts the 64-character hexadecimal SHA-256 hash from the decoded QR text.
    Handles both raw hash strings and structured JSON payloads.
    """
    cleaned = payload.strip()

    # Try parsing as JSON first
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            for key in ["hash", "sha256_hash", "sha256", "digest"]:
                if key in data and len(data[key]) == 64:
                    return data[key].lower()
    except Exception:
        pass

    # If it's a 64-char hex string directly
    if len(cleaned) == 64 and all(c in "0123456789abcdefABCDEF" for c in cleaned):
        return cleaned.lower()

    # Search for 64-character continuous hex pattern
    import re
    match = re.search(r"\b[a-fA-F0-9]{64}\b", cleaned)
    if match:
        return match.group(0).lower()

    # Fallback to returning raw payload
    return cleaned
