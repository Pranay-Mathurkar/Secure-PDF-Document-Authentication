"""Tampering localization and visualization for document page images."""
import logging
from pathlib import Path

import cv2
import numpy as np

from app.dsp_config import get_dsp_config
from app.services.preprocessing_service import (
    DSPProcessingError,
    preprocess_image,
    validate_image_array,
)


logger = logging.getLogger(__name__)


def validate_tamper_score(score: float) -> float:
    """Validate a normalized tamper score."""
    try:
        numeric_score = float(score)
    except (TypeError, ValueError) as exc:
        raise DSPProcessingError("tamper score must be numeric.") from exc
    if not 0.0 <= numeric_score <= 1.0:
        raise DSPProcessingError("tamper score must be between 0.0 and 1.0.")
    return numeric_score


def get_tamper_detection_config() -> dict:
    """Return localization and morphology configuration values."""
    config = get_dsp_config()
    return {
        "tampering_threshold": config["tampering_threshold"],
        "minimum_region_area": config["minimum_region_area"],
        "difference_threshold": config["difference_threshold"],
        "morphology_kernel_size": config["tamper_morphology_kernel_size"],
        "morphology_iterations": config["tamper_morphology_iterations"],
        "alignment_max_shift": config["tamper_alignment_max_shift"],
    }


def _prepare_grayscale(image: np.ndarray, preprocess: bool = True) -> np.ndarray:
    validate_image_array(image, "tampering image")
    prepared = preprocess_image(image) if preprocess else image
    if prepared.ndim != 2:
        raise DSPProcessingError("Tampering analysis requires grayscale images.")
    return np.clip(prepared, 0, 255).astype(np.uint8, copy=False)


def align_images(
    original_image: np.ndarray,
    verification_image: np.ndarray,
    preprocess: bool = True,
    max_shift: float | None = None,
) -> tuple[np.ndarray, np.ndarray, tuple[float, float]]:
    """
    Align pages using size normalization and phase correlation translation.

    A candidate with different dimensions is resized once to the reference
    dimensions using area interpolation. Phase correlation then estimates only
    translation; shifts beyond ``max_shift`` are rejected to avoid distortion.
    No rotation, perspective warp, or non-uniform deformation is applied.
    """
    original = _prepare_grayscale(original_image, preprocess)
    verification = _prepare_grayscale(verification_image, preprocess)
    config = get_tamper_detection_config()
    shift_limit = config["alignment_max_shift"] if max_shift is None else float(max_shift)
    if shift_limit < 0:
        raise DSPProcessingError("max_shift must not be negative.")
    if verification.shape != original.shape:
        verification = cv2.resize(
            verification,
            (original.shape[1], original.shape[0]),
            interpolation=cv2.INTER_AREA,
        )
    try:
        shift, _ = cv2.phaseCorrelate(
            original.astype(np.float32),
            verification.astype(np.float32),
        )
        shift_x, shift_y = float(shift[0]), float(shift[1])
        if abs(shift_x) > shift_limit or abs(shift_y) > shift_limit:
            shift_x, shift_y = 0.0, 0.0
        matrix = np.array([[1.0, 0.0, shift_x], [0.0, 1.0, shift_y]], dtype=np.float32)
        aligned = cv2.warpAffine(
            verification,
            matrix,
            (original.shape[1], original.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return original, aligned, (shift_x, shift_y)
    except MemoryError:
        logger.exception("Memory error while aligning tampering images.")
        raise
    except Exception as exc:
        logger.exception("Failed to align tampering images.")
        raise DSPProcessingError(f"Failed to align tampering images: {exc}") from exc


def calculate_difference_image(
    original_image: np.ndarray,
    verification_image: np.ndarray,
    preprocess: bool = True,
) -> dict:
    """Return aligned images and their absolute uint8 difference image."""
    original, aligned, shift = align_images(
        original_image,
        verification_image,
        preprocess=preprocess,
    )
    difference = cv2.absdiff(original, aligned)
    return {
        "original": original,
        "aligned_verification": aligned,
        "difference": difference,
        "shift": shift,
    }


def create_tampering_mask(
    difference_image: np.ndarray,
    threshold: int | None = None,
    kernel_size: int | None = None,
    iterations: int | None = None,
) -> np.ndarray:
    """Threshold and clean an absolute difference image morphologically."""
    if (
        not isinstance(difference_image, np.ndarray)
        or difference_image.ndim != 2
        or difference_image.size == 0
    ):
        raise DSPProcessingError("Difference image must be a non-empty 2D array.")
    config = get_tamper_detection_config()
    threshold_value = config["difference_threshold"] if threshold is None else int(threshold)
    kernel_value = config["morphology_kernel_size"] if kernel_size is None else int(kernel_size)
    iteration_value = config["morphology_iterations"] if iterations is None else int(iterations)
    if not 0 <= threshold_value <= 255:
        raise DSPProcessingError("Difference threshold must be between 0 and 255.")
    if kernel_value <= 0 or kernel_value % 2 == 0:
        raise DSPProcessingError("Morphology kernel size must be a positive odd number.")
    if iteration_value < 0:
        raise DSPProcessingError("Morphology iterations must not be negative.")
    _, mask = cv2.threshold(
        difference_image.astype(np.uint8, copy=False),
        threshold_value,
        255,
        cv2.THRESH_BINARY,
    )
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (kernel_value, kernel_value),
    )
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=iteration_value)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=iteration_value)
    mask = cv2.dilate(mask, kernel, iterations=iteration_value)
    return cv2.erode(mask, kernel, iterations=iteration_value)


def detect_tampered_regions(
    tampering_mask: np.ndarray,
    minimum_region_area: int | None = None,
) -> list[dict]:
    """Find external connected regions and return filtered bounding boxes."""
    if not isinstance(tampering_mask, np.ndarray) or tampering_mask.ndim != 2:
        raise DSPProcessingError("Tampering mask must be a 2D NumPy array.")
    minimum_area = (
        get_tamper_detection_config()["minimum_region_area"]
        if minimum_region_area is None
        else int(minimum_region_area)
    )
    if minimum_area < 0:
        raise DSPProcessingError("minimum_region_area must not be negative.")
    contours, _ = cv2.findContours(
        tampering_mask.astype(np.uint8, copy=False),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    regions = []
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < minimum_area:
            continue
        x, y, width, height = cv2.boundingRect(contour)
        regions.append({
            "x": int(x),
            "y": int(y),
            "width": int(width),
            "height": int(height),
            "area": area,
        })
    return sorted(regions, key=lambda region: (region["y"], region["x"]))


def create_bounding_box_image(
    original_image: np.ndarray,
    regions: list[dict],
) -> np.ndarray:
    """Draw red bounding boxes around detected regions."""
    validate_image_array(original_image, "bounding-box source image")
    if original_image.ndim == 2:
        output = cv2.cvtColor(
            np.clip(original_image, 0, 255).astype(np.uint8),
            cv2.COLOR_GRAY2BGR,
        )
    else:
        output = np.clip(original_image, 0, 255).astype(np.uint8).copy()
    for region in regions:
        x, y = region["x"], region["y"]
        width, height = region["width"], region["height"]
        cv2.rectangle(output, (x, y), (x + width - 1, y + height - 1), (0, 0, 255), 2)
    return output


def create_tampering_heatmap(difference_image: np.ndarray) -> np.ndarray:
    """Create a BGR heatmap where blue is low and red is high difference."""
    if not isinstance(difference_image, np.ndarray) or difference_image.ndim != 2:
        raise DSPProcessingError("Difference image must be a 2D NumPy array.")
    return cv2.applyColorMap(
        np.clip(difference_image, 0, 255).astype(np.uint8),
        cv2.COLORMAP_JET,
    )


def localize_tampering(
    original_image: np.ndarray,
    verification_image: np.ndarray,
    threshold: int | None = None,
    minimum_region_area: int | None = None,
    output_dir: str | Path | None = None,
    page_number: int = 1,
) -> dict:
    """Run complete localization and optionally write four visual artifacts."""
    comparison = calculate_difference_image(original_image, verification_image)
    mask = create_tampering_mask(comparison["difference"], threshold=threshold)
    regions = detect_tampered_regions(mask, minimum_region_area=minimum_region_area)
    outputs = {
        "difference_image": comparison["difference"],
        "tampering_mask": mask,
        "bounding_box_image": create_bounding_box_image(
            comparison["original"], regions
        ),
        "tampering_heatmap": create_tampering_heatmap(comparison["difference"]),
    }
    output_paths = {}
    if output_dir is not None:
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        for name, image in outputs.items():
            path = directory / f"page_{page_number}_{name}.png"
            if not cv2.imwrite(str(path), image):
                raise DSPProcessingError(f"Failed to write tampering output: {path}")
            output_paths[name] = str(path)
    return {
        "page": page_number,
        "regions": regions,
        "region_count": len(regions),
        "alignment_shift": comparison["shift"],
        "outputs": outputs,
        "output_paths": output_paths,
    }


def analyze_tampering_pages(
    original_pages: list[np.ndarray],
    verification_pages: list[np.ndarray],
    threshold: int | None = None,
    minimum_region_area: int | None = None,
    output_dir: str | Path | None = None,
) -> dict:
    """Localize modifications across corresponding pages."""
    if len(original_pages) != len(verification_pages):
        raise DSPProcessingError("Documents must have the same number of pages.")
    if not original_pages:
        raise DSPProcessingError("No pages were provided for tampering analysis.")
    pages = [
        localize_tampering(
            original,
            verification,
            threshold=threshold,
            minimum_region_area=minimum_region_area,
            output_dir=output_dir,
            page_number=page_number,
        )
        for page_number, (original, verification) in enumerate(
            zip(original_pages, verification_pages), start=1
        )
    ]
    return {
        "pages": pages,
        "modified_pages": [page["page"] for page in pages if page["regions"]],
        "total_region_count": sum(page["region_count"] for page in pages),
    }
