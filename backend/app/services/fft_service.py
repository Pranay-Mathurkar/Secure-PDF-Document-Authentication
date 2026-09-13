"""
FFT analysis infrastructure.
Phase 1 provides validation hooks only; FFT analysis is reserved for a later phase.
"""
import logging

import numpy as np

from app.services.preprocessing_service import validate_image_array


logger = logging.getLogger(__name__)


def validate_fft_input(image: np.ndarray) -> np.ndarray:
    """Validate an image before future FFT analysis."""
    logger.debug("Validating image for future FFT analysis.")
    return validate_image_array(image, "FFT input image")
