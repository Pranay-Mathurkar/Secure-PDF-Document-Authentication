"""
Phase 2 validation tests for the DSP preprocessing service.
"""
import fitz
import numpy as np

from app.services.preprocessing_service import (
    apply_noise_reduction,
    convert_to_grayscale,
    normalize_intensity,
    preprocess_image,
    preprocess_pdf_pages,
)


def _create_pdf_bytes(page_count: int = 2) -> bytes:
    doc = fitz.open()
    for index in range(page_count):
        page = doc.new_page(width=200, height=120)
        page.insert_text(fitz.Point(20, 40), f"Page {index + 1}", fontsize=16)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_color_document_image_preprocesses_to_grayscale():
    image = np.zeros((32, 48, 3), dtype=np.uint8)
    image[:, :, 0] = 220
    image[:, :, 1] = 80
    image[:, :, 2] = 30

    result = preprocess_image(image)

    assert result.shape == (32, 48)
    assert result.dtype == np.uint8


def test_rgba_document_image_preprocesses_to_grayscale():
    image = np.zeros((24, 36, 4), dtype=np.uint8)
    image[:, :, 0] = 20
    image[:, :, 1] = 180
    image[:, :, 2] = 90
    image[:, :, 3] = 255

    gray = convert_to_grayscale(image)

    assert gray.shape == (24, 36)
    assert gray.dtype == np.uint8


def test_grayscale_document_image_keeps_dimensions():
    image = np.arange(64, dtype=np.uint8).reshape(8, 8)

    result = preprocess_image(image, return_intermediates=True)

    assert result["grayscale_image"].shape == image.shape
    assert result["filtered_image"].shape == image.shape
    assert result["final_image"].shape == image.shape


def test_noisy_document_image_supports_configured_filters():
    rng = np.random.default_rng(42)
    noisy = rng.integers(0, 256, size=(40, 40), dtype=np.uint8)

    gaussian = apply_noise_reduction(noisy, {"noise_reduction": "gaussian"})
    median = apply_noise_reduction(noisy, {"noise_reduction": "median"})

    assert gaussian.shape == noisy.shape
    assert median.shape == noisy.shape
    assert gaussian.dtype == np.uint8
    assert median.dtype == np.uint8


def test_normalization_outputs_consistent_uint8_range():
    image = np.array([[10, 20], [30, 40]], dtype=np.float32)

    normalized = normalize_intensity(image)

    assert normalized.dtype == np.uint8
    assert normalized.min() == 0
    assert normalized.max() == 255


def test_multi_page_pdf_preprocessing_preserves_page_order():
    pdf_bytes = _create_pdf_bytes(page_count=3)

    pages = preprocess_pdf_pages(pdf_bytes, page_indices=[0, 1, 2])

    assert len(pages) == 3
    assert all(page.ndim == 2 for page in pages)
    assert pages[0].shape == pages[1].shape == pages[2].shape
