"""
Image similarity analysis service.
Calculates MSE, PSNR, and SSIM for preprocessed document images.
"""
import logging
import math

import numpy as np
from skimage.metrics import structural_similarity

from app.dsp_config import get_dsp_config
from app.services.preprocessing_service import (
    DSPProcessingError,
    preprocess_image,
    validate_image_array,
)


logger = logging.getLogger(__name__)


def validate_similarity_inputs(
    reference_image: np.ndarray,
    candidate_image: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Validate and prepare two images before similarity analysis.

    Strategy:
        Images are converted through the preprocessing pipeline and must have
        identical final dimensions. The service does not resize mismatched
        images because document scale/layout changes are meaningful evidence.
    """
    try:
        validate_image_array(reference_image, "reference image")
        validate_image_array(candidate_image, "candidate image")
        prepared_reference = preprocess_image(reference_image)
        prepared_candidate = preprocess_image(candidate_image)

        if prepared_reference.shape != prepared_candidate.shape:
            raise DSPProcessingError(
                "reference image and candidate image must have identical "
                "preprocessed dimensions; automatic resizing is intentionally disabled."
            )
    except MemoryError:
        logger.exception("Memory error while validating similarity inputs.")
        raise
    except DSPProcessingError as exc:
        logger.error("Invalid similarity inputs: %s", exc)
        raise
    except Exception as exc:
        logger.exception("Unexpected similarity validation error.")
        raise DSPProcessingError(f"Failed to validate similarity inputs: {exc}") from exc

    return prepared_reference, prepared_candidate


def get_similarity_config() -> dict:
    """Return similarity-related configuration values."""
    config = get_dsp_config()
    return {
        "ssim_threshold": config["ssim_threshold"],
        "difference_threshold": config["difference_threshold"],
    }


def calculate_mse(reference_image: np.ndarray, candidate_image: np.ndarray) -> float:
    """
    Calculate mean squared error between two compatible document images.
    """
    reference, candidate = validate_similarity_inputs(reference_image, candidate_image)

    try:
        difference = reference.astype(np.float64) - candidate.astype(np.float64)
        return float(np.mean(np.square(difference)))
    except MemoryError:
        logger.exception("Memory error while calculating MSE.")
        raise
    except Exception as exc:
        logger.exception("Failed to calculate MSE.")
        raise DSPProcessingError(f"Failed to calculate MSE: {exc}") from exc


def calculate_psnr(
    reference_image: np.ndarray,
    candidate_image: np.ndarray,
    max_pixel_value: float = 255.0,
) -> float:
    """
    Calculate peak signal-to-noise ratio in decibels.

    Returns math.inf when images are identical and MSE is zero.
    """
    mse = calculate_mse(reference_image, candidate_image)
    if mse == 0:
        return math.inf

    try:
        return float(20.0 * math.log10(float(max_pixel_value) / math.sqrt(mse)))
    except Exception as exc:
        logger.exception("Failed to calculate PSNR.")
        raise DSPProcessingError(f"Failed to calculate PSNR: {exc}") from exc


def calculate_ssim(reference_image: np.ndarray, candidate_image: np.ndarray) -> float:
    """
    Calculate structural similarity index between two document images.

    The returned score is typically in the 0.0 to 1.0 range, where 1.0 means
    identical images.
    """
    reference, candidate = validate_similarity_inputs(reference_image, candidate_image)

    try:
        min_dimension = min(reference.shape[:2])
        if min_dimension < 7:
            raise DSPProcessingError("SSIM requires images of at least 7x7 pixels.")

        score = structural_similarity(reference, candidate, data_range=255)
        return float(score)
    except MemoryError:
        logger.exception("Memory error while calculating SSIM.")
        raise
    except DSPProcessingError as exc:
        logger.error("Invalid SSIM inputs: %s", exc)
        raise
    except Exception as exc:
        logger.exception("Failed to calculate SSIM.")
        raise DSPProcessingError(f"Failed to calculate SSIM: {exc}") from exc


def compare_images(reference_image: np.ndarray, candidate_image: np.ndarray) -> dict:
    """
    Compare two document images and return MSE, PSNR, and SSIM metrics.
    """
    reference, candidate = validate_similarity_inputs(reference_image, candidate_image)

    try:
        difference = reference.astype(np.float64) - candidate.astype(np.float64)
        mse = float(np.mean(np.square(difference)))
        psnr = math.inf if mse == 0 else float(20.0 * math.log10(255.0 / math.sqrt(mse)))

        min_dimension = min(reference.shape[:2])
        if min_dimension < 7:
            raise DSPProcessingError("SSIM requires images of at least 7x7 pixels.")
        ssim = float(structural_similarity(reference, candidate, data_range=255))

        return {
            "mse": mse,
            "psnr": psnr,
            "ssim": ssim,
        }
    except MemoryError:
        logger.exception("Memory error while comparing images.")
        raise
    except DSPProcessingError as exc:
        logger.error("Image comparison failed: %s", exc)
        raise
    except Exception as exc:
        logger.exception("Failed to compare images.")
        raise DSPProcessingError(f"Failed to compare images: {exc}") from exc


def compare_image_pages(
    reference_pages: list[np.ndarray],
    candidate_pages: list[np.ndarray],
) -> dict:
    """
    Compare document pages pairwise while preserving page order.

    Page 1 is compared with Page 1, Page 2 with Page 2, and so on. Page counts
    must match; no insertion/deletion alignment is attempted in this phase.
    """
    if len(reference_pages) != len(candidate_pages):
        raise DSPProcessingError("reference and candidate documents must have the same page count.")

    page_results = []
    for page_index, (reference_page, candidate_page) in enumerate(
        zip(reference_pages, candidate_pages),
        start=1,
    ):
        metrics = compare_images(reference_page, candidate_page)
        page_results.append({
            "page_number": page_index,
            **metrics,
        })

    if not page_results:
        raise DSPProcessingError("No pages were provided for comparison.")

    return {
        "pages": page_results,
        "overall_mse": float(np.mean([page["mse"] for page in page_results])),
        "overall_psnr": float(np.mean([page["psnr"] for page in page_results])),
        "overall_ssim": float(np.mean([page["ssim"] for page in page_results])),
    }
