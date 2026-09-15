"""Frequency-domain analysis for preprocessed document page images."""
import logging

import numpy as np

from app.dsp_config import get_dsp_config
from app.services.preprocessing_service import (
    DSPProcessingError,
    preprocess_image,
    validate_image_array,
)


logger = logging.getLogger(__name__)


def validate_fft_input(image: np.ndarray) -> np.ndarray:
    """Validate an image before FFT analysis."""
    return validate_image_array(image, "FFT input image")


def get_fft_config() -> dict:
    """Return configurable FFT analysis values."""
    return {"low_frequency_ratio": get_dsp_config()["fft_low_frequency_ratio"]}


def _prepare_image(image: np.ndarray, preprocess: bool) -> np.ndarray:
    validate_fft_input(image)
    prepared = preprocess_image(image) if preprocess else image
    if prepared.ndim != 2:
        raise DSPProcessingError("FFT analysis requires a 2D grayscale image.")
    return prepared.astype(np.float64, copy=False)


def _validate_low_frequency_ratio(value: float) -> float:
    try:
        ratio = float(value)
    except (TypeError, ValueError) as exc:
        raise DSPProcessingError("low_frequency_ratio must be a number.") from exc
    if not 0.0 < ratio <= 0.5:
        raise DSPProcessingError("low_frequency_ratio must be greater than 0 and at most 0.5.")
    return ratio


def calculate_fft(image: np.ndarray, preprocess: bool = True) -> np.ndarray:
    """Calculate a centered 2D FFT for one document image."""
    prepared = _prepare_image(image, preprocess)
    try:
        return np.fft.fftshift(np.fft.fft2(prepared))
    except MemoryError:
        logger.exception("Memory error while calculating FFT.")
        raise
    except Exception as exc:
        logger.exception("Failed to calculate FFT.")
        raise DSPProcessingError(f"Failed to calculate FFT: {exc}") from exc


def calculate_magnitude_spectrum(
    fft_result: np.ndarray,
    normalize: bool = False,
) -> np.ndarray:
    """
    Calculate ``log(1 + abs(FFT))``.

    When requested, safely normalize the result to uint8 for frontend display.
    """
    if not isinstance(fft_result, np.ndarray) or fft_result.size == 0:
        raise DSPProcessingError("FFT result must be a non-empty NumPy array.")
    if fft_result.ndim != 2:
        raise DSPProcessingError("FFT result must be a 2D array.")
    try:
        spectrum = np.log1p(np.abs(fft_result)).astype(np.float64, copy=False)
        if not normalize:
            return spectrum
        # PDF pages have a very large DC component. Full min/max scaling lets
        # that single peak compress nearly all other frequencies into gray.
        # Percentile clipping preserves the useful spectral structure for
        # dashboard visualization while leaving the raw feature path intact.
        minimum = float(np.percentile(spectrum, 1.0))
        maximum = float(np.percentile(spectrum, 99.5))
        if maximum <= minimum:
            return np.zeros(spectrum.shape, dtype=np.uint8)
        scaled = (spectrum - minimum) * (255.0 / (maximum - minimum))
        clipped = np.clip(scaled, 0, 255) / 255.0
        enhanced = np.sqrt(clipped) * 255.0
        return np.clip(enhanced, 0, 255).astype(np.uint8)
    except MemoryError:
        logger.exception("Memory error while calculating magnitude spectrum.")
        raise
    except Exception as exc:
        logger.exception("Failed to calculate magnitude spectrum.")
        raise DSPProcessingError(f"Failed to calculate magnitude spectrum: {exc}") from exc


def _features_from_fft(fft_result: np.ndarray, low_frequency_ratio: float) -> dict:
    ratio = _validate_low_frequency_ratio(low_frequency_ratio)
    magnitude = calculate_magnitude_spectrum(fft_result)
    power = np.square(np.abs(fft_result))
    height, width = power.shape
    half_height = max(1, int(round(height * ratio / 2.0)))
    half_width = max(1, int(round(width * ratio / 2.0)))
    center_y, center_x = height // 2, width // 2
    low_mask = np.zeros(power.shape, dtype=bool)
    low_mask[
        max(0, center_y - half_height):min(height, center_y + half_height + 1),
        max(0, center_x - half_width):min(width, center_x + half_width + 1),
    ] = True
    low_energy = float(np.sum(power[low_mask]))
    high_energy = float(np.sum(power[~low_mask]))
    return {
        "mean_frequency_magnitude": float(np.mean(magnitude)),
        "standard_deviation": float(np.std(magnitude)),
        "total_spectral_energy": float(np.sum(power)),
        "low_frequency_energy": low_energy,
        "high_frequency_energy": high_energy,
        "high_to_low_frequency_ratio": float(high_energy / max(low_energy, np.finfo(float).eps)),
        "low_frequency_ratio": ratio,
    }


def extract_frequency_features(
    image: np.ndarray,
    low_frequency_ratio: float | None = None,
    preprocess: bool = True,
) -> dict:
    """Extract interpretable spectral features from one document image."""
    config_ratio = get_fft_config()["low_frequency_ratio"]
    fft_result = calculate_fft(image, preprocess=preprocess)
    return _features_from_fft(
        fft_result,
        config_ratio if low_frequency_ratio is None else low_frequency_ratio,
    )


def _coerce_features(features_or_image, low_frequency_ratio: float | None) -> dict:
    if isinstance(features_or_image, dict):
        return features_or_image
    return extract_frequency_features(
        features_or_image,
        low_frequency_ratio=low_frequency_ratio,
    )


def compare_frequency_features(
    original,
    verification,
    low_frequency_ratio: float | None = None,
) -> float:
    """
    Compare feature dictionaries or images and return a 0-100 similarity score.

    Each feature uses a symmetric relative difference:
    ``similarity = 1 - abs(a-b) / (abs(a)+abs(b)+epsilon)``. The mean of all
    six comparable features is clamped to [0, 100], making the score stable,
    bounded, and interpretable (100 means identical features).
    """
    original_features = _coerce_features(original, low_frequency_ratio)
    verification_features = _coerce_features(verification, low_frequency_ratio)
    feature_names = (
        "mean_frequency_magnitude",
        "standard_deviation",
        "total_spectral_energy",
        "low_frequency_energy",
        "high_frequency_energy",
        "high_to_low_frequency_ratio",
    )
    try:
        similarities = []
        for name in feature_names:
            first = float(original_features[name])
            second = float(verification_features[name])
            denominator = abs(first) + abs(second) + np.finfo(float).eps
            similarities.append(max(0.0, 1.0 - abs(first - second) / denominator))
        return float(np.clip(np.mean(similarities) * 100.0, 0.0, 100.0))
    except (KeyError, TypeError, ValueError) as exc:
        raise DSPProcessingError("Frequency features have an invalid shape.") from exc


def analyze_frequency_pages(
    original_pages: list[np.ndarray],
    verification_pages: list[np.ndarray],
    low_frequency_ratio: float | None = None,
) -> dict:
    """Analyze corresponding pages and return page-level and overall scores."""
    if len(original_pages) != len(verification_pages):
        raise DSPProcessingError("Documents must have the same number of pages.")
    if not original_pages:
        raise DSPProcessingError("No pages were provided for FFT analysis.")
    results = []
    for page_number, (original, verification) in enumerate(
        zip(original_pages, verification_pages), start=1
    ):
        features = extract_frequency_features(original, low_frequency_ratio)
        score = compare_frequency_features(
            features,
            extract_frequency_features(verification, low_frequency_ratio),
        )
        results.append({
            "page": page_number,
            "page_number": page_number,
            "features": features,
            "frequency_similarity": score,
        })
    return {
        "pages": results,
        "overall_frequency_similarity": float(
            np.mean([result["frequency_similarity"] for result in results])
        ),
    }


def generate_magnitude_spectrum_image(
    image: np.ndarray,
    preprocess: bool = True,
) -> np.ndarray:
    """Return a normalized uint8 FFT magnitude spectrum for frontend display."""
    return calculate_magnitude_spectrum(
        calculate_fft(image, preprocess=preprocess),
        normalize=True,
    )
