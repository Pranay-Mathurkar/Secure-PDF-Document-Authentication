"""Phase 5 tests for DCT frequency-domain analysis."""
import numpy as np

from app.services.dct_service import (
    analyze_dct_pages,
    calculate_dct,
    compare_dct_features,
    extract_dct_features,
)


def _document_image() -> np.ndarray:
    image = np.full((64, 64), 255, dtype=np.uint8)
    image[10:54, 14:18] = 0
    image[10:14, 14:48] = 0
    image[30:34, 14:42] = 0
    return image


def test_dct_uses_float32_and_extracts_requested_features():
    dct_result = calculate_dct(_document_image())
    features = extract_dct_features(_document_image())

    assert dct_result.shape == (64, 64)
    assert dct_result.dtype == np.float32
    assert set(features) >= {
        "dc_coefficient",
        "total_energy",
        "low_frequency_energy",
        "mid_frequency_energy",
        "high_frequency_energy",
    }
    assert features["total_energy"] > 0


def test_identical_images_have_perfect_dct_similarity():
    image = _document_image()
    features = extract_dct_features(image)

    assert compare_dct_features(features, features) == 100.0


def test_modifications_reduce_dct_similarity_reasonably():
    reference = _document_image()
    small_change = reference.copy()
    small_change[20:24, 22:26] = 180
    large_change = reference.copy()
    large_change[8:56, 8:56] = 0
    different = np.random.default_rng(4).integers(0, 256, (64, 64), dtype=np.uint8)

    small_score = compare_dct_features(reference, small_change)
    large_score = compare_dct_features(reference, large_change)
    different_score = compare_dct_features(reference, different)

    assert 0 <= different_score < large_score < small_score < 100


def test_multi_page_dct_analysis_returns_page_and_overall_results():
    first = _document_image()
    second = np.rot90(first).copy()
    result = analyze_dct_pages([first, second], [first.copy(), second.copy()])

    assert len(result["pages"]) == 2
    assert result["pages"][0]["page"] == 1
    assert result["pages"][1]["features"]["dc_coefficient"] > 0
    assert result["overall_dct_similarity"] == 100.0
