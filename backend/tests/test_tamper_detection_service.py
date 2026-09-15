"""Phase 8 tests for tampering localization and visualization."""
from pathlib import Path

import cv2
import numpy as np

from app.services.tamper_detection_service import (
    align_images,
    analyze_tampering_pages,
    create_tampering_mask,
    detect_tampered_regions,
    localize_tampering,
)


def _document_image() -> np.ndarray:
    image = np.full((100, 120), 255, dtype=np.uint8)
    image[15:85, 20:24] = 0
    image[15:19, 20:90] = 0
    image[45:49, 20:80] = 0
    return image


def test_small_translation_is_aligned_without_rotation_or_distortion():
    original = _document_image()
    matrix = np.float32([[1, 0, 2], [0, 1, 1]])
    shifted = cv2.warpAffine(original, matrix, (120, 100), borderValue=255)

    aligned_original, aligned_candidate, shift = align_images(original, shifted)

    assert aligned_original.shape == aligned_candidate.shape == original.shape
    assert abs(shift[0]) <= 10
    assert abs(shift[1]) <= 10


def test_small_text_change_produces_a_filtered_region():
    original = _document_image()
    modified = original.copy()
    modified[60:68, 55:65] = 0

    result = localize_tampering(original, modified, threshold=20, minimum_region_area=10)

    assert result["region_count"] >= 1
    assert result["outputs"]["difference_image"].shape == original.shape
    assert result["outputs"]["tampering_mask"].dtype == np.uint8
    assert result["outputs"]["bounding_box_image"].shape[:2] == original.shape
    assert result["outputs"]["tampering_heatmap"].shape[:2] == original.shape


def test_large_and_multiple_modifications_are_localized():
    original = _document_image()
    modified = original.copy()
    modified[5:25, 90:110] = 0
    modified[70:95, 45:75] = 0

    result = localize_tampering(original, modified, threshold=20, minimum_region_area=10)

    assert result["region_count"] >= 2
    assert all(
        {"x", "y", "width", "height", "area"} <= set(region)
        for region in result["regions"]
    )


def test_clean_page_has_no_regions_and_outputs_can_be_written(tmp_path: Path):
    image = _document_image()
    result = localize_tampering(
        image,
        image.copy(),
        output_dir=tmp_path,
        page_number=2,
    )

    assert result["region_count"] == 0
    assert len(list(tmp_path.glob("page_2_*.png"))) == 4


def test_multi_page_localization_reports_modified_pages():
    original = _document_image()
    modified = original.copy()
    modified[60:75, 55:75] = 0

    result = analyze_tampering_pages(
        [original, original],
        [modified, original.copy()],
        threshold=20,
        minimum_region_area=10,
    )

    assert result["modified_pages"] == [1]
    assert len(result["pages"]) == 2
