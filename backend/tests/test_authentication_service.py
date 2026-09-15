"""Phase 9 tests for the multi-layer authentication decision engine."""
import numpy as np
import pytest

from app.services.authentication_service import (
    authenticate_documents,
    validate_authentication_weights,
)
from app.services.preprocessing_service import DSPProcessingError


def _document_image() -> np.ndarray:
    image = np.full((64, 64), 255, dtype=np.uint8)
    image[10:54, 14:18] = 0
    image[10:14, 14:48] = 0
    image[30:34, 14:42] = 0
    return image


def _authenticate(candidate, expected_hash="same", calculated_hash="same"):
    return authenticate_documents(
        [_document_image()],
        [candidate],
        expected_hash,
        calculated_hash,
        tampering_threshold=20,
        minimum_region_area=10,
    )


def test_exact_original_is_authentic_when_hash_matches():
    result = _authenticate(_document_image())

    assert result["hash"]["status"] == "MATCH"
    assert result["status"] == "AUTHENTIC"
    assert result["confidence_score"] == 100.0
    assert result["pages"][0]["similarity"]["ssim"] > 0.999


def test_hash_mismatch_with_identical_visuals_is_rendering_difference():
    result = _authenticate(
        _document_image(),
        expected_hash="original",
        calculated_hash="different",
    )

    assert result["status"] == "AUTHENTIC_WITH_RENDERING_DIFFERENCES"
    assert result["visual_confidence_score"] == 100.0
    assert result["confidence_score"] == 60.0


def test_small_rendering_difference_is_not_called_significant_tampering():
    candidate = _document_image()
    candidate[20:24, 22:26] = 180

    result = _authenticate(candidate, expected_hash="original", calculated_hash="changed")

    assert result["hash"]["status"] == "MISMATCH"
    assert result["status"] in {
        "AUTHENTIC_WITH_RENDERING_DIFFERENCES",
        "SUSPICIOUS",
        "MODIFIED",
    }
    assert result["status"] != "SIGNIFICANTLY_TAMPERED"


def test_large_tampering_is_significant():
    candidate = _document_image()
    candidate[8:56, 8:56] = 0

    result = _authenticate(candidate, expected_hash="original", calculated_hash="changed")

    assert result["tampering"]["detected"] is True
    assert result["tampering"]["total_region_count"] >= 1
    assert result["status"] in {"MODIFIED", "SIGNIFICANTLY_TAMPERED"}
    assert result["confidence_score"] < 70.0


def test_multi_page_result_identifies_modified_page():
    original = _document_image()
    modified = original.copy()
    modified[45:60, 40:55] = 0
    result = authenticate_documents(
        [original, original],
        [original.copy(), modified],
        "a",
        "b",
        tampering_threshold=20,
        minimum_region_area=10,
    )

    assert len(result["pages"]) == 2
    assert result["tampering"]["modified_pages"] == [2]
    assert result["pages"][0]["tampering"]["detected"] is False


def test_weights_must_sum_to_one():
    with pytest.raises(DSPProcessingError, match="sum to 1.0"):
        validate_authentication_weights({
            "hash": 0.5,
            "ssim": 0.25,
            "fft": 0.15,
            "dct": 0.10,
            "edge": 0.20,
        })
