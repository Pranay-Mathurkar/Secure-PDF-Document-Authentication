"""
PDF Processing and Document Synthesis Service using PyMuPDF.
Handles first-page extraction, aesthetic authentication page generation, and 2-page merging.
"""
from datetime import datetime
import fitz  # PyMuPDF


def create_authentication_page_doc(
    sha256_hash: str,
    timestamp_str: str,
    qr_png_bytes: bytes,
    algorithm: str = "SHA-256"
) -> fitz.Document:
    """
    Creates a dedicated A4 authentication certificate page containing:
    - Project Title
    - 'Document Authentication QR' Header
    - Embedded High-Contrast QR Code
    - SHA-256 Cryptographic Digest
    - Timestamp & Algorithm Telemetry
    - Academic Disclaimer & Verification Instructions

    Returns:
        fitz.Document: Single-page PyMuPDF document.
    """
    # A4 standard dimensions: 595.32 x 841.92 pt
    a4_width, a4_height = 595.0, 842.0
    auth_doc = fitz.open()
    page = auth_doc.new_page(width=a4_width, height=a4_height)

    # 1. Background Header Banner (Deep Navy #0F172A)
    header_rect = fitz.Rect(0, 0, a4_width, 100)
    page.draw_rect(header_rect, color=None, fill=(15 / 255, 23 / 255, 42 / 255))

    # Header Accent Bar (Blue #2563EB)
    accent_bar = fitz.Rect(0, 96, a4_width, 100)
    page.draw_rect(accent_bar, color=None, fill=(37 / 255, 99 / 255, 235 / 255))

    # Header Text
    page.insert_text(
        fitz.Point(36, 45),
        "SECURE PDF DOCUMENT AUTHENTICATION",
        fontname="helv",
        fontsize=16,
        color=(1, 1, 1),
    )
    page.insert_text(
        fitz.Point(36, 70),
        "Document Authentication QR Certificate - Page 2",
        fontname="helv",
        fontsize=11,
        color=(148 / 255, 163 / 255, 184 / 255),
    )

    # 2. Main Outer Card Border
    card_rect = fitz.Rect(36, 125, a4_width - 36, 750)
    page.draw_rect(card_rect, color=(226 / 255, 232 / 255, 240 / 255), width=1.5)

    # 3. Section Title
    page.insert_text(
        fitz.Point(56, 155),
        "Cryptographic Integrity Seal",
        fontname="helv",
        fontsize=14,
        color=(15 / 255, 23 / 255, 42 / 255),
    )
    page.insert_text(
        fitz.Point(56, 175),
        "Scan the QR code below using the verification portal to authenticate Page 1.",
        fontname="helv",
        fontsize=9.5,
        color=(100 / 255, 116 / 255, 139 / 255),
    )

    # 4. QR Code Insertion (Centered)
    qr_size = 200.0
    qr_x0 = (a4_width - qr_size) / 2.0
    qr_y0 = 205.0
    qr_rect = fitz.Rect(qr_x0, qr_y0, qr_x0 + qr_size, qr_y0 + qr_size)

    # QR Code background frame
    qr_frame = fitz.Rect(qr_x0 - 10, qr_y0 - 10, qr_x0 + qr_size + 10, qr_y0 + qr_size + 10)
    page.draw_rect(qr_frame, color=(203 / 255, 213 / 255, 225 / 255), fill=(248 / 255, 250 / 255, 252 / 255), width=1)

    page.insert_image(qr_rect, stream=qr_png_bytes)

    # 5. SHA-256 Digest Box
    hash_box_y0 = 445.0
    hash_box = fitz.Rect(56, hash_box_y0, a4_width - 56, hash_box_y0 + 75)
    page.draw_rect(hash_box, color=(226 / 255, 232 / 255, 240 / 255), fill=(241 / 255, 245 / 255, 249 / 255), width=1)

    page.insert_text(
        fitz.Point(70, hash_box_y0 + 22),
        "CANONICAL SHA-256 HASH (PAGE 1):",
        fontname="helv",
        fontsize=9,
        color=(71 / 255, 85 / 255, 105 / 255),
    )

    # Split 64-char hash into two lines for clean aesthetic readability
    hash_line1 = sha256_hash[:32]
    hash_line2 = sha256_hash[32:]
    page.insert_text(
        fitz.Point(70, hash_box_y0 + 44),
        hash_line1,
        fontname="courier",
        fontsize=11.5,
        color=(15 / 255, 23 / 255, 42 / 255),
    )
    page.insert_text(
        fitz.Point(70, hash_box_y0 + 62),
        hash_line2,
        fontname="courier",
        fontsize=11.5,
        color=(15 / 255, 23 / 255, 42 / 255),
    )

    # 6. Metadata Telemetry Details
    meta_y0 = 545.0
    labels = [
        ("Cryptographic Algorithm:", f"{algorithm} (Deterministic 150 DPI RGB)"),
        ("Securing Timestamp:", timestamp_str),
        ("Authentication Scope:", "First Page Visual Canonical Layer"),
        ("Error Correction Level:", "QR Code Level H (30% Recovery Resistance)"),
    ]

    for i, (label, val) in enumerate(labels):
        current_y = meta_y0 + (i * 24)
        page.insert_text(
            fitz.Point(56, current_y),
            label,
            fontname="helv",
            fontsize=9.5,
            color=(100 / 255, 116 / 255, 139 / 255),
        )
        page.insert_text(
            fitz.Point(220, current_y),
            val,
            fontname="helv",
            fontsize=9.5,
            color=(15 / 255, 23 / 255, 42 / 255),
        )

    # 7. Verification Notice Footer
    notice_rect = fitz.Rect(56, 665, a4_width - 56, 730)
    page.draw_rect(notice_rect, color=(191 / 255, 219 / 255, 254 / 255), fill=(239 / 255, 246 / 255, 255 / 255), width=1)

    page.insert_text(
        fitz.Point(70, 685),
        "ACADEMIC VERIFICATION NOTICE",
        fontname="helv",
        fontsize=8.5,
        color=(30 / 255, 64 / 255, 175 / 255),
    )
    page.insert_text(
        fitz.Point(70, 703),
        "This PDF was generated by the Cryptographic PDF Document Authentication System.",
        fontname="helv",
        fontsize=8,
        color=(30 / 255, 58 / 255, 138 / 255),
    )
    page.insert_text(
        fitz.Point(70, 717),
        "Any modification to the textual or graphical content of Page 1 triggers immediate hash failure.",
        fontname="helv",
        fontsize=8,
        color=(30 / 255, 58 / 255, 138 / 255),
    )

    # Footer Watermark
    page.insert_text(
        fitz.Point(36, 775),
        f"Generated: {timestamp_str} | Academic Document Forensics Framework",
        fontname="helv",
        fontsize=8,
        color=(148 / 255, 163 / 255, 184 / 255),
    )

    return auth_doc


def assemble_secured_pdf(
    original_pdf_bytes: bytes,
    sha256_hash: str,
    timestamp_str: str,
    qr_png_bytes: bytes,
    algorithm: str = "SHA-256"
) -> bytes:
    """
    Combines the first page of the original PDF with the newly synthesized
    authentication QR page into a 2-page secured PDF.

    Args:
        original_pdf_bytes (bytes): Binary bytes of the source PDF.
        sha256_hash (str): Deterministic hash of Page 1.
        timestamp_str (str): Generation timestamp.
        qr_png_bytes (bytes): High-error-correction QR PNG image bytes.
        algorithm (str): Name of the hash algorithm.

    Returns:
        bytes: The combined 2-page secured PDF binary bytes.
    """
    orig_doc = fitz.open(stream=original_pdf_bytes, filetype="pdf")
    if orig_doc.page_count < 1:
        raise ValueError("The uploaded PDF does not contain any readable pages.")

    # Create destination document
    final_doc = fitz.open()

    # Step 1: Copy Page 1 (index 0)
    final_doc.insert_pdf(orig_doc, from_page=0, to_page=0)

    # Step 2: Create Authentication Page 2
    auth_doc = create_authentication_page_doc(
        sha256_hash=sha256_hash,
        timestamp_str=timestamp_str,
        qr_png_bytes=qr_png_bytes,
        algorithm=algorithm,
    )

    # Step 3: Append Authentication Page as Page 2
    final_doc.insert_pdf(auth_doc, from_page=0, to_page=0)

    # Serialize to bytes
    pdf_bytes = final_doc.tobytes(deflate=True, garbage=3)

    orig_doc.close()
    auth_doc.close()
    final_doc.close()

    return pdf_bytes
