"""Structural and frequency-domain document feature extraction."""
import logging

import cv2
import numpy as np

from app.dsp_config import get_dsp_config
from app.services.dct_service import extract_dct_features
from app.services.fft_service import extract_frequency_features
from app.services.preprocessing_service import (
    DSPProcessingError,
    preprocess_image,
    validate_image_array,
)


logger = logging.getLogger(__name__)


def validate_feature_input(image: np.ndarray) -> np.ndarray:
    """Validate an image before document feature extraction."""
    return validate_image_array(image, "feature extraction input image")


def get_feature_config() -> dict:
    """Return configurable feature-extraction values."""
    config = get_dsp_config()
    return {
        "image_resolution": config["image_resolution"],
        "block_size": config["block_size"],
        "canny_lower_threshold": config["canny_lower_threshold"],
        "canny_upper_threshold": config["canny_upper_threshold"],
    }


def _prepare_grayscale(image: np.ndarray, preprocess: bool = True) -> np.ndarray:
    validate_feature_input(image)
    prepared = preprocess_image(image) if preprocess else image
    if prepared.ndim != 2:
        raise DSPProcessingError("Feature extraction requires a 2D grayscale image.")
    if prepared.dtype != np.uint8:
        prepared = np.clip(prepared, 0, 255).astype(np.uint8)
    return prepared


def calculate_sobel_edges(
    image: np.ndarray,
    preprocess: bool = True,
) -> dict:
    """Calculate horizontal, vertical, and combined Sobel gradients."""
    gray = _prepare_grayscale(image, preprocess)
    try:
        gray_float = gray.astype(np.float32, copy=False)
        horizontal = cv2.Sobel(gray_float, cv2.CV_32F, 1, 0, ksize=3)
        vertical = cv2.Sobel(gray_float, cv2.CV_32F, 0, 1, ksize=3)
        magnitude = cv2.magnitude(horizontal, vertical)
        return {
            "horizontal_gradient": horizontal,
            "vertical_gradient": vertical,
            "magnitude": magnitude,
        }
    except MemoryError:
        logger.exception("Memory error while calculating Sobel edges.")
        raise
    except Exception as exc:
        logger.exception("Failed to calculate Sobel edges.")
        raise DSPProcessingError(f"Failed to calculate Sobel edges: {exc}") from exc


def calculate_canny_edges(
    image: np.ndarray,
    lower_threshold: int | None = None,
    upper_threshold: int | None = None,
    preprocess: bool = True,
) -> np.ndarray:
    """Calculate a binary Canny edge map using configurable thresholds."""
    gray = _prepare_grayscale(image, preprocess)
    config = get_feature_config()
    lower = config["canny_lower_threshold"] if lower_threshold is None else lower_threshold
    upper = config["canny_upper_threshold"] if upper_threshold is None else upper_threshold
    try:
        lower = int(lower)
        upper = int(upper)
    except (TypeError, ValueError) as exc:
        raise DSPProcessingError("Canny thresholds must be integers.") from exc
    if not 0 <= lower < upper <= 255:
        raise DSPProcessingError(
            "Canny thresholds must satisfy 0 <= lower < upper <= 255."
        )
    try:
        return cv2.Canny(gray, lower, upper)
    except MemoryError:
        logger.exception("Memory error while calculating Canny edges.")
        raise
    except Exception as exc:
        logger.exception("Failed to calculate Canny edges.")
        raise DSPProcessingError(f"Failed to calculate Canny edges: {exc}") from exc


def calculate_edge_density(edge_map: np.ndarray) -> float:
    """Return the normalized proportion of non-zero edge pixels."""
    if not isinstance(edge_map, np.ndarray) or edge_map.ndim != 2 or edge_map.size == 0:
        raise DSPProcessingError("Edge map must be a non-empty 2D NumPy array.")
    return float(np.count_nonzero(edge_map) / edge_map.size)


def compare_edge_maps(
    original_edge_map: np.ndarray,
    verification_edge_map: np.ndarray,
) -> float:
    """
    Compare binary edge maps with Dice similarity and return 0-100.

    Dice similarity is 2*intersection/(edges_a + edges_b). Two empty maps
    are considered identical and return 100.
    """
    if (
        not isinstance(original_edge_map, np.ndarray)
        or not isinstance(verification_edge_map, np.ndarray)
        or original_edge_map.ndim != 2
        or verification_edge_map.ndim != 2
        or original_edge_map.shape != verification_edge_map.shape
    ):
        raise DSPProcessingError("Edge maps must be 2D arrays with equal dimensions.")
    original = original_edge_map.astype(bool, copy=False)
    verification = verification_edge_map.astype(bool, copy=False)
    original_count = int(np.count_nonzero(original))
    verification_count = int(np.count_nonzero(verification))
    if original_count + verification_count == 0:
        return 100.0
    intersection = int(np.count_nonzero(original & verification))
    return float(np.clip(200.0 * intersection / (original_count + verification_count), 0, 100))


def extract_document_feature_vector(
    image: np.ndarray,
    canny_lower_threshold: int | None = None,
    canny_upper_threshold: int | None = None,
    preprocess: bool = True,
) -> dict:
    """
    Extract reusable intensity, edge, FFT, and DCT features.

    The image is preprocessed once; frequency services receive that prepared
    grayscale image to avoid duplicating preprocessing work.
    """
    gray = _prepare_grayscale(image, preprocess)
    sobel = calculate_sobel_edges(gray, preprocess=False)
    canny = calculate_canny_edges(
        gray,
        lower_threshold=canny_lower_threshold,
        upper_threshold=canny_upper_threshold,
        preprocess=False,
    )
    return {
        "mean_intensity": float(np.mean(gray)),
        "std_intensity": float(np.std(gray)),
        "edge_density": calculate_edge_density(canny),
        "sobel_edge_density": calculate_edge_density(sobel["magnitude"]),
        "fft_features": extract_frequency_features(gray, preprocess=False),
        "dct_features": extract_dct_features(gray, preprocess=False),
        "edge_map": canny,
    }


def compare_document_feature_vectors(
    original: dict,
    verification: dict,
) -> float:
    """Compare the edge maps stored in two document feature vectors."""
    if "edge_map" not in original or "edge_map" not in verification:
        raise DSPProcessingError("Feature vectors must contain edge maps.")
    return compare_edge_maps(original["edge_map"], verification["edge_map"])


def analyze_feature_pages(
    original_pages: list[np.ndarray],
    verification_pages: list[np.ndarray],
    canny_lower_threshold: int | None = None,
    canny_upper_threshold: int | None = None,
) -> dict:
    """Extract and compare structural feature vectors page by page."""
    if len(original_pages) != len(verification_pages):
        raise DSPProcessingError("Documents must have the same number of pages.")
    if not original_pages:
        raise DSPProcessingError("No pages were provided for feature analysis.")
    pages = []
    for page_number, (original, verification) in enumerate(
        zip(original_pages, verification_pages), start=1
    ):
        original_features = extract_document_feature_vector(
            original, canny_lower_threshold, canny_upper_threshold
        )
        verification_features = extract_document_feature_vector(
            verification, canny_lower_threshold, canny_upper_threshold
        )
        pages.append({
            "page": page_number,
            "page_number": page_number,
            "features": original_features,
            "edge_similarity": compare_document_feature_vectors(
                original_features, verification_features
            ),
        })
    return {
        "pages": pages,
        "overall_edge_similarity": float(
            np.mean([page["edge_similarity"] for page in pages])
        ),
    }
