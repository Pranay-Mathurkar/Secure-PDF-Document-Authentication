"""Phase 4 tests for FFT frequency-domain analysis."""
import numpy as np

from app.services.fft_service import (
    analyze_frequency_pages,
    calculate_fft,
    calculate_magnitude_spectrum,
    compare_frequency_features,
    extract_frequency_features,
    generate_magnitude_spectrum_image,
)


def _document_image() -> np.ndarray:
    image = np.full((64, 64), 255, dtype=np.uint8)
    image[10:54, 14:18] = 0
    image[10:14, 14:48] = 0
    image[30:34, 14:42] = 0
    return image


def test_fft_is_centered_and_spectrum_can_be_visualized():
    result = calculate_fft(_document_image())
    spectrum = calculate_magnitude_spectrum(result)
    display = generate_magnitude_spectrum_image(_document_image())

    assert result.shape == (64, 64)
    assert spectrum.shape == (64, 64)
    assert display.dtype == np.uint8
    assert 0 <= display.min() <= display.max() <= 255


def test_identical_images_have_perfect_frequency_similarity():
    image = _document_image()
    features = extract_frequency_features(image)

    assert compare_frequency_features(features, features) == 100.0


def test_modifications_reduce_frequency_similarity_reasonably():
    reference = _document_image()
    small_change = reference.copy()
    small_change[20:24, 22:26] = 180
    large_change = reference.copy()
    large_change[8:56, 8:56] = 0
    different = np.random.default_rng(4).integers(0, 256, (64, 64), dtype=np.uint8)

    small_score = compare_frequency_features(reference, small_change)
    large_score = compare_frequency_features(reference, large_change)
    different_score = compare_frequency_features(reference, different)

    assert 0 <= different_score < large_score < small_score < 100


def test_multi_page_analysis_returns_page_features_and_overall_score():
    first = _document_image()
    second = np.rot90(first).copy()
    result = analyze_frequency_pages([first, second], [first.copy(), second.copy()])

    assert len(result["pages"]) == 2
    assert result["pages"][0]["page"] == 1
    assert result["pages"][1]["features"]["total_spectral_energy"] > 0
    assert result["overall_frequency_similarity"] == 100.0
