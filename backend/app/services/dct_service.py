"""Discrete cosine transform analysis for preprocessed document page images."""
import logging

import cv2
import numpy as np

from app.dsp_config import get_dsp_config
from app.services.preprocessing_service import (
    DSPProcessingError,
    preprocess_image,
    validate_image_array,
)


logger = logging.getLogger(__name__)


def validate_dct_input(image: np.ndarray) -> np.ndarray:
    """Validate an image before DCT analysis."""
    return validate_image_array(image, "DCT input image")


def get_dct_config() -> dict:
    """Return configurable DCT frequency-region boundaries."""
    config = get_dsp_config()
    return {
        "low_frequency_ratio": config["dct_low_frequency_ratio"],
        "mid_frequency_ratio": config["dct_mid_frequency_ratio"],
    }


def _validate_region_ratios(low_frequency_ratio: float, mid_frequency_ratio: float) -> tuple[float, float]:
    try:
        low = float(low_frequency_ratio)
        mid = float(mid_frequency_ratio)
    except (TypeError, ValueError) as exc:
        raise DSPProcessingError("DCT region ratios must be numbers.") from exc
    if not 0.0 < low < mid <= 1.0:
        raise DSPProcessingError(
            "DCT region ratios must satisfy 0 < low_frequency_ratio "
            "< mid_frequency_ratio <= 1."
        )
    return low, mid


def _prepare_image(image: np.ndarray, preprocess: bool) -> np.ndarray:
    validate_dct_input(image)
    prepared = preprocess_image(image) if preprocess else image
    if prepared.ndim != 2:
        raise DSPProcessingError("DCT analysis requires a 2D grayscale image.")

    try:
        values = prepared.astype(np.float32, copy=False)
        if not np.all(np.isfinite(values)):
            raise DSPProcessingError("DCT input image contains non-finite values.")
        maximum = float(np.max(values))
        if maximum <= 1.0:
            normalized = values
        else:
            normalized = values / 255.0
        return np.clip(normalized, 0.0, 1.0).astype(np.float32, copy=False)
    except MemoryError:
        logger.exception("Memory error while preparing DCT input.")
        raise
    except DSPProcessingError:
        raise
    except Exception as exc:
        logger.exception("Failed to prepare DCT input.")
        raise DSPProcessingError(f"Failed to prepare DCT input: {exc}") from exc


def calculate_dct(image: np.ndarray, preprocess: bool = True) -> np.ndarray:
    """Calculate a 2D DCT-II matrix from a normalized grayscale image."""
    prepared = _prepare_image(image, preprocess)
    try:
        return cv2.dct(prepared)
    except MemoryError:
        logger.exception("Memory error while calculating DCT.")
        raise
    except Exception as exc:
        logger.exception("Failed to calculate DCT.")
        raise DSPProcessingError(f"Failed to calculate DCT: {exc}") from exc


def _features_from_dct(
    dct_result: np.ndarray,
    low_frequency_ratio: float,
    mid_frequency_ratio: float,
) -> dict:
    if not isinstance(dct_result, np.ndarray) or dct_result.size == 0:
        raise DSPProcessingError("DCT result must be a non-empty NumPy array.")
    if dct_result.ndim != 2:
        raise DSPProcessingError("DCT result must be a 2D array.")
    low, mid = _validate_region_ratios(low_frequency_ratio, mid_frequency_ratio)

    height, width = dct_result.shape
    low_rows = max(1, int(np.ceil(height * low)))
    low_columns = max(1, int(np.ceil(width * low)))
    mid_rows = max(low_rows, int(np.ceil(height * mid)))
    mid_columns = max(low_columns, int(np.ceil(width * mid)))
    energy = np.square(dct_result.astype(np.float64, copy=False))

    low_region = energy[:low_rows, :low_columns]
    mid_region = energy[:mid_rows, :mid_columns].copy()
    mid_region[:low_rows, :low_columns] = 0.0
    high_region = energy.copy()
    high_region[:mid_rows, :mid_columns] = 0.0

    return {
        "dc_coefficient": float(dct_result[0, 0]),
        "total_energy": float(np.sum(energy)),
        "low_frequency_energy": float(np.sum(low_region)),
        "mid_frequency_energy": float(np.sum(mid_region)),
        "high_frequency_energy": float(np.sum(high_region)),
        "low_frequency_ratio": low,
        "mid_frequency_ratio": mid,
    }


def extract_dct_features(
    image: np.ndarray,
    low_frequency_ratio: float | None = None,
    mid_frequency_ratio: float | None = None,
    preprocess: bool = True,
) -> dict:
    """Extract DC and configurable low/mid/high DCT energy features."""
    config = get_dct_config()
    dct_result = calculate_dct(image, preprocess=preprocess)
    return _features_from_dct(
        dct_result,
        config["low_frequency_ratio"] if low_frequency_ratio is None else low_frequency_ratio,
        config["mid_frequency_ratio"] if mid_frequency_ratio is None else mid_frequency_ratio,
    )


def _coerce_features(features_or_image, low_frequency_ratio, mid_frequency_ratio) -> dict:
    if isinstance(features_or_image, dict):
        return features_or_image
    return extract_dct_features(
        features_or_image,
        low_frequency_ratio=low_frequency_ratio,
        mid_frequency_ratio=mid_frequency_ratio,
    )


def compare_dct_features(
    original,
    verification,
    low_frequency_ratio: float | None = None,
    mid_frequency_ratio: float | None = None,
) -> float:
    """
    Compare DCT features and return a bounded 0-100 similarity score.

    For each feature, symmetric relative difference is converted to similarity:
    ``1 - abs(a-b) / (abs(a)+abs(b)+epsilon)``. The mean of the five requested
    features is multiplied by 100 and clamped, so identical features score 100.
    """
    original_features = _coerce_features(
        original, low_frequency_ratio, mid_frequency_ratio
    )
    verification_features = _coerce_features(
        verification, low_frequency_ratio, mid_frequency_ratio
    )
    feature_names = (
        "dc_coefficient",
        "total_energy",
        "low_frequency_energy",
        "mid_frequency_energy",
        "high_frequency_energy",
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
        raise DSPProcessingError("DCT features have an invalid shape.") from exc


def analyze_dct_pages(
    original_pages: list[np.ndarray],
    verification_pages: list[np.ndarray],
    low_frequency_ratio: float | None = None,
    mid_frequency_ratio: float | None = None,
) -> dict:
    """Analyze corresponding document pages and return aggregate similarity."""
    if len(original_pages) != len(verification_pages):
        raise DSPProcessingError("Documents must have the same number of pages.")
    if not original_pages:
        raise DSPProcessingError("No pages were provided for DCT analysis.")

    results = []
    for page_number, (original, verification) in enumerate(
        zip(original_pages, verification_pages), start=1
    ):
        original_features = extract_dct_features(
            original, low_frequency_ratio, mid_frequency_ratio
        )
        verification_features = extract_dct_features(
            verification, low_frequency_ratio, mid_frequency_ratio
        )
        results.append({
            "page": page_number,
            "page_number": page_number,
            "features": original_features,
            "dct_similarity": compare_dct_features(
                original_features, verification_features
            ),
        })

    overall = float(np.mean([result["dct_similarity"] for result in results]))
    return {
        "pages": results,
        "overall_dct_similarity": overall,
    }
