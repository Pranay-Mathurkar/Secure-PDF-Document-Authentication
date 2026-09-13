"""
DCT analysis infrastructure.
Phase 1 provides validation hooks only; DCT analysis is reserved for a later phase.
"""
import logging

import numpy as np

from app.dsp_config import get_dsp_config
from app.services.preprocessing_service import validate_image_array


logger = logging.getLogger(__name__)


def validate_dct_input(image: np.ndarray) -> np.ndarray:
    """Validate an image before future DCT analysis."""
    logger.debug("Validating image for future DCT analysis.")
    return validate_image_array(image, "DCT input image")


def get_dct_config() -> dict:
    """Return DCT-related configuration values."""
    config = get_dsp_config()
    return {"block_size": config["block_size"]}
