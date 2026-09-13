"""
DSP image preprocessing service.
Provides reusable preprocessing for images rendered from PDF pages.
"""
import logging

import cv2
import fitz  # PyMuPDF
import numpy as np

from app.dsp_config import get_dsp_config


logger = logging.getLogger(__name__)


class DSPProcessingError(ValueError):
    """Raised when an image cannot be processed by the DSP pipeline."""


def validate_image_array(image: np.ndarray, context: str = "image") -> np.ndarray:
    """
    Validate an image matrix before DSP operations.

    Args:
        image (np.ndarray): Image matrix in grayscale or channel format.
        context (str): Human-readable label used in error messages.

    Returns:
        np.ndarray: The original image when validation succeeds.
    """
    try:
        if image is None:
            raise DSPProcessingError(f"{context} is missing.")
        if not isinstance(image, np.ndarray):
            raise DSPProcessingError(f"{context} must be a NumPy array.")
        if image.size == 0:
            raise DSPProcessingError(f"{context} is empty.")
        if image.ndim not in (2, 3):
            raise DSPProcessingError(f"{context} must be a 2D grayscale or 3D color image.")
        if image.ndim == 3 and image.shape[2] not in (1, 3, 4):
            raise DSPProcessingError(f"{context} has an unsupported channel count.")
        if not np.issubdtype(image.dtype, np.number):
            raise DSPProcessingError(f"{context} must contain numeric pixel values.")
    except MemoryError:
        logger.exception("Memory error while validating %s.", context)
        raise
    except DSPProcessingError:
        logger.exception("Invalid DSP input: %s.", context)
        raise
    except Exception as exc:
        logger.exception("Unexpected image validation error for %s.", context)
        raise DSPProcessingError(f"Failed to validate {context}: {exc}") from exc

    return image


def get_preprocessing_config() -> dict:
    """Return preprocessing-related configuration values."""
    config = get_dsp_config()
    return {
        "image_resolution": config["image_resolution"],
        "noise_reduction": config["noise_reduction"],
        "gaussian_kernel_size": config["gaussian_kernel_size"],
        "median_filter_kernel_size": config["median_filter_kernel_size"],
        "histogram_enhancement": config["histogram_enhancement"],
        "clahe_clip_limit": config["clahe_clip_limit"],
        "clahe_tile_grid_size": config["clahe_tile_grid_size"],
    }


def _merge_config(config: dict | None = None) -> dict:
    merged = get_preprocessing_config()
    if config:
        merged.update(config)
    return merged


def _validate_odd_kernel_size(value: int, field_name: str) -> int:
    try:
        kernel_size = int(value)
    except (TypeError, ValueError) as exc:
        raise DSPProcessingError(f"{field_name} must be an integer.") from exc

    if kernel_size <= 0:
        raise DSPProcessingError(f"{field_name} must be greater than zero.")
    if kernel_size % 2 == 0:
        raise DSPProcessingError(f"{field_name} must be an odd number.")
    return kernel_size


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert RGB, RGBA, single-channel, or grayscale images to uint8 grayscale.
    """
    validate_image_array(image, "image for grayscale conversion")

    try:
        if image.ndim == 2:
            gray = image
        elif image.shape[2] == 1:
            gray = image[:, :, 0]
        elif image.shape[2] == 3:
            gray = cv2.cvtColor(image.astype(np.uint8, copy=False), cv2.COLOR_RGB2GRAY)
        elif image.shape[2] == 4:
            gray = cv2.cvtColor(image.astype(np.uint8, copy=False), cv2.COLOR_RGBA2GRAY)
        else:
            raise DSPProcessingError("Unsupported image channel count.")
    except MemoryError:
        logger.exception("Memory error during grayscale conversion.")
        raise
    except DSPProcessingError:
        logger.exception("Invalid image for grayscale conversion.")
        raise
    except Exception as exc:
        logger.exception("Failed to convert image to grayscale.")
        raise DSPProcessingError(f"Failed to convert image to grayscale: {exc}") from exc

    return normalize_intensity(gray)


def apply_noise_reduction(image: np.ndarray, config: dict | None = None) -> np.ndarray:
    """
    Apply one configured noise-reduction filter.

    Supported values:
        None / "none": no filtering
        "gaussian": Gaussian blur
        "median": median filtering
    """
    validate_image_array(image, "image for noise reduction")
    effective_config = _merge_config(config)
    method = effective_config.get("noise_reduction")

    if method is None:
        return image

    method = str(method).strip().lower()
    if method in ("", "none"):
        return image

    try:
        if method == "gaussian":
            kernel_size = _validate_odd_kernel_size(
                effective_config["gaussian_kernel_size"],
                "gaussian_kernel_size",
            )
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        if method == "median":
            kernel_size = _validate_odd_kernel_size(
                effective_config["median_filter_kernel_size"],
                "median_filter_kernel_size",
            )
            return cv2.medianBlur(image, kernel_size)
    except MemoryError:
        logger.exception("Memory error during noise reduction.")
        raise
    except DSPProcessingError:
        logger.exception("Invalid noise-reduction configuration.")
        raise
    except Exception as exc:
        logger.exception("Failed to apply noise reduction.")
        raise DSPProcessingError(f"Failed to apply noise reduction: {exc}") from exc

    raise DSPProcessingError(f"Unsupported noise reduction method: {method}.")


def normalize_intensity(image: np.ndarray) -> np.ndarray:
    """
    Normalize image intensity to the 0-255 uint8 range using min-max scaling.
    """
    validate_image_array(image, "image for intensity normalization")

    try:
        image_float = image.astype(np.float32, copy=False)
        min_value = float(np.min(image_float))
        max_value = float(np.max(image_float))

        if max_value == min_value:
            return np.zeros(image.shape, dtype=np.uint8)

        normalized = (image_float - min_value) * (255.0 / (max_value - min_value))
        return np.clip(normalized, 0, 255).astype(np.uint8)
    except MemoryError:
        logger.exception("Memory error during intensity normalization.")
        raise
    except Exception as exc:
        logger.exception("Failed to normalize image intensity.")
        raise DSPProcessingError(f"Failed to normalize image intensity: {exc}") from exc


def apply_histogram_enhancement(image: np.ndarray, config: dict | None = None) -> np.ndarray:
    """
    Optionally apply histogram enhancement.

    Supported values:
        None / "none": no enhancement
        "equalization": global histogram equalization
        "clahe": contrast-limited adaptive histogram equalization
    """
    validate_image_array(image, "image for histogram enhancement")
    effective_config = _merge_config(config)
    method = effective_config.get("histogram_enhancement")

    if method is None:
        return image

    method = str(method).strip().lower()
    if method in ("", "none"):
        return image

    try:
        gray = normalize_intensity(image)
        if method == "equalization":
            return cv2.equalizeHist(gray)
        if method == "clahe":
            tile_size = int(effective_config["clahe_tile_grid_size"])
            if tile_size <= 0:
                raise DSPProcessingError("clahe_tile_grid_size must be greater than zero.")
            clahe = cv2.createCLAHE(
                clipLimit=float(effective_config["clahe_clip_limit"]),
                tileGridSize=(tile_size, tile_size),
            )
            return clahe.apply(gray)
    except MemoryError:
        logger.exception("Memory error during histogram enhancement.")
        raise
    except DSPProcessingError:
        logger.exception("Invalid histogram enhancement configuration.")
        raise
    except Exception as exc:
        logger.exception("Failed to apply histogram enhancement.")
        raise DSPProcessingError(f"Failed to apply histogram enhancement: {exc}") from exc

    raise DSPProcessingError(f"Unsupported histogram enhancement method: {method}.")


def preprocess_image(
    image: np.ndarray,
    config: dict | None = None,
    return_intermediates: bool = False,
    include_original: bool = False,
) -> np.ndarray | dict:
    """
    Run the reusable preprocessing pipeline on one image.

    Returns the final processed image by default. When return_intermediates is
    True, returns a dictionary with selected pipeline stages.
    """
    effective_config = _merge_config(config)

    try:
        validate_image_array(image, "preprocessing input image")
        grayscale_image = convert_to_grayscale(image)
        filtered_image = apply_noise_reduction(grayscale_image, effective_config)
        enhanced_image = apply_histogram_enhancement(filtered_image, effective_config)
        final_image = normalize_intensity(enhanced_image)
    except MemoryError:
        logger.exception("Memory error in preprocessing pipeline.")
        raise
    except DSPProcessingError:
        logger.exception("Preprocessing pipeline failed.")
        raise
    except Exception as exc:
        logger.exception("Unexpected preprocessing pipeline error.")
        raise DSPProcessingError(f"Preprocessing pipeline failed: {exc}") from exc

    if not return_intermediates:
        return final_image

    result = {
        "grayscale_image": grayscale_image,
        "filtered_image": filtered_image,
        "final_image": final_image,
    }
    if include_original:
        result["original_image"] = image
    if effective_config.get("histogram_enhancement") not in (None, "", "none"):
        result["enhanced_image"] = enhanced_image
    return result


def render_page_to_image(page: fitz.Page, dpi: int | None = None) -> np.ndarray:
    """
    Render a PDF page to an RGB NumPy array for DSP preprocessing.
    """
    try:
        if dpi is None:
            dpi = get_preprocessing_config()["image_resolution"]
        zoom = float(dpi) / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False)
        return np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
            pixmap.height,
            pixmap.width,
            3,
        ).copy()
    except MemoryError:
        logger.exception("Memory error while rendering PDF page for preprocessing.")
        raise
    except Exception as exc:
        logger.exception("Failed to render PDF page for preprocessing.")
        raise DSPProcessingError(f"Failed to render PDF page: {exc}") from exc


def preprocess_pdf_pages(
    pdf_bytes: bytes,
    page_indices: list[int] | None = None,
    config: dict | None = None,
    return_intermediates: bool = False,
) -> list[np.ndarray | dict]:
    """
    Render and preprocess PDF pages independently while preserving page order.
    """
    if not pdf_bytes:
        raise DSPProcessingError("PDF bytes are empty.")

    results: list[np.ndarray | dict] = []
    effective_config = _merge_config(config)

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            if doc.page_count == 0:
                raise DSPProcessingError("PDF does not contain any pages.")

            if page_indices is None:
                ordered_indices = list(range(doc.page_count))
            else:
                ordered_indices = list(page_indices)

            for page_index in ordered_indices:
                if page_index < 0 or page_index >= doc.page_count:
                    raise DSPProcessingError(f"Page index out of range: {page_index}.")
                image = render_page_to_image(
                    doc[page_index],
                    dpi=effective_config["image_resolution"],
                )
                results.append(
                    preprocess_image(
                        image,
                        effective_config,
                        return_intermediates=return_intermediates,
                    )
                )
        finally:
            doc.close()
    except MemoryError:
        logger.exception("Memory error while preprocessing PDF pages.")
        raise
    except DSPProcessingError:
        logger.exception("PDF page preprocessing failed.")
        raise
    except Exception as exc:
        logger.exception("Failed to preprocess PDF pages.")
        raise DSPProcessingError(f"Failed to preprocess PDF pages: {exc}") from exc

    return results
