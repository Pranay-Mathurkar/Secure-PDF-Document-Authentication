"""
Feature extraction infrastructure.
Phase 1 validates inputs and exposes configuration for later feature work.
"""
import logging

import numpy as np

from app.dsp_config import get_dsp_config
from app.services.preprocessing_service import validate_image_array


logger = logging.getLogger(__name__)


def validate_feature_input(image: np.ndarray) -> np.ndarray:
    """Validate an image before future feature extraction."""
    logger.debug("Validating image for future feature extraction.")
    return validate_image_array(image, "feature extraction input image")


def get_feature_config() -> dict:
    """Return feature-extraction configuration values."""
    config = get_dsp_config()
    return {
        "image_resolution": config["image_resolution"],
        "block_size": config["block_size"],
    }
