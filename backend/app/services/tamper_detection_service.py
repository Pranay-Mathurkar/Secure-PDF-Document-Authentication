"""
Tamper detection infrastructure.
Phase 1 exposes thresholds and validation hooks only.
"""
import logging

from app.dsp_config import get_dsp_config
from app.services.preprocessing_service import DSPProcessingError


logger = logging.getLogger(__name__)


def validate_tamper_score(score: float) -> float:
    """Validate a normalized tamper score for future decision logic."""
    try:
        numeric_score = float(score)
    except (TypeError, ValueError) as exc:
        logger.exception("Invalid tamper score.")
        raise DSPProcessingError("tamper score must be numeric.") from exc

    if numeric_score < 0.0 or numeric_score > 1.0:
        logger.error("Tamper score outside normalized range: %s", numeric_score)
        raise DSPProcessingError("tamper score must be between 0.0 and 1.0.")

    return numeric_score


def get_tamper_detection_config() -> dict:
    """Return tamper-detection configuration values."""
    config = get_dsp_config()
    return {
        "tampering_threshold": config["tampering_threshold"],
        "minimum_region_area": config["minimum_region_area"],
        "difference_threshold": config["difference_threshold"],
    }
