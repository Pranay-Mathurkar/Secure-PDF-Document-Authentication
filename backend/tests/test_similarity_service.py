"""
Phase 3 validation tests for the image similarity service.
"""
import math

import numpy as np

from app.services.preprocessing_service import DSPProcessingError
from app.services.similarity_service import (
    calculate_mse,
    calculate_psnr,
    calculate_ssim,
    compare_image_pages,
    compare_images,
)


def _base_document_image() -> np.ndarray:
    image = np.full((64, 64), 255, dtype=np.uint8)
    image[10:54, 14:18] = 0
    image[10:14, 14:48] = 0
    image[30:34, 14:42] = 0
    return image


def test_identical_image_metrics_are_exact_or_near_perfect():
    image = _base_document_image()

    result = compare_images(image, image.copy())

    assert result["mse"] == 0.0
    assert math.isinf(result["psnr"])
    assert result["ssim"] > 0.999


def test_slightly_modified_image_has_small_difference():
    reference = _base_document_image()
    candidate = reference.copy()
    candidate[20:24, 22:26] = 180

    result = compare_images(reference, candidate)

    assert result["mse"] > 0.0
    assert result["mse"] < 300.0
    assert result["psnr"] > 20.0
    assert result["ssim"] > 0.90


def test_significantly_modified_image_has_larger_difference():
    reference = _base_document_image()
    candidate = reference.copy()
    candidate[8:56, 8:56] = 0

    result = compare_images(reference, candidate)

    assert result["mse"] > 1000.0
    assert result["psnr"] < 20.0
    assert result["ssim"] < 0.80


def test_metric_functions_return_numeric_values():
    reference = _base_document_image()
    candidate = reference.copy()
    candidate[4:12, 4:12] = 80

    assert calculate_mse(reference, candidate) > 0.0
    assert calculate_psnr(reference, candidate) > 0.0
    assert 0.0 <= calculate_ssim(reference, candidate) <= 1.0


def test_page_wise_comparison_returns_overall_averages():
    page_1 = _base_document_image()
    page_2 = np.rot90(page_1).copy()
    candidate_page_2 = page_2.copy()
    candidate_page_2[20:28, 20:28] = 128

    result = compare_image_pages([page_1, page_2], [page_1.copy(), candidate_page_2])

    assert len(result["pages"]) == 2
    assert result["pages"][0]["page_number"] == 1
    assert result["pages"][1]["page_number"] == 2
    assert result["overall_mse"] >= 0.0
    assert result["overall_ssim"] <= 1.0


def test_dimension_mismatch_is_rejected_without_resizing():
    reference = np.zeros((64, 64), dtype=np.uint8)
    candidate = np.zeros((32, 64), dtype=np.uint8)

    try:
        compare_images(reference, candidate)
    except DSPProcessingError as exc:
        assert "automatic resizing is intentionally disabled" in str(exc)
    else:
        raise AssertionError("Expected dimension mismatch to raise DSPProcessingError.")
