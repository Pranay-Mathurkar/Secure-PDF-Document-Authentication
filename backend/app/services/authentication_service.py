"""Multi-layer document authentication decision engine.

SHA-256 remains the cryptographic authority. DSP results add forensic context
and classify documents when the cryptographic hashes do not match.
"""
import hmac
import math

import numpy as np

from app.dsp_config import get_dsp_config
from app.services.dct_service import compare_dct_features, extract_dct_features
from app.services.feature_service import (
    compare_edge_maps,
    extract_document_feature_vector,
)
from app.services.fft_service import (
    compare_frequency_features,
    extract_frequency_features,
)
from app.services.preprocessing_service import DSPProcessingError
from app.services.similarity_service import compare_images
from app.services.tamper_detection_service import localize_tampering


_WEIGHTED_FEATURES = ("hash", "ssim", "fft", "dct", "edge")


def get_authentication_config() -> dict:
    """Return authentication weights and configurable status thresholds."""
    config = get_dsp_config()
    return {
        "weights": dict(config["authentication_weights"]),
        "rendering_threshold": config["authentication_rendering_threshold"],
        "suspicious_threshold": config["authentication_suspicious_threshold"],
        "significant_threshold": config["authentication_significant_threshold"],
        "tampering_percentage_threshold": config[
            "authentication_tampering_percentage_threshold"
        ],
    }


def validate_authentication_weights(weights: dict | None = None) -> dict:
    """Validate that all confidence weights are non-negative and sum to one."""
    effective = get_authentication_config()["weights"] if weights is None else dict(weights)
    if set(effective) != set(_WEIGHTED_FEATURES):
        raise DSPProcessingError(
            f"Authentication weights must contain exactly: {', '.join(_WEIGHTED_FEATURES)}."
        )
    try:
        numeric = {name: float(effective[name]) for name in _WEIGHTED_FEATURES}
    except (TypeError, ValueError) as exc:
        raise DSPProcessingError("Authentication weights must be numeric.") from exc
    if any(value < 0.0 for value in numeric.values()):
        raise DSPProcessingError("Authentication weights must not be negative.")
    if not math.isclose(sum(numeric.values()), 1.0, abs_tol=1e-9):
        raise DSPProcessingError("Authentication weights must sum to 1.0.")
    return numeric


def _page_tampering_percentage(mask: np.ndarray) -> float:
    return float(np.count_nonzero(mask) * 100.0 / mask.size)


def _status_for_hash_mismatch(
    visual_confidence: float,
    tampering_detected: bool,
    tampering_percentage: float,
    config: dict,
) -> str:
    if (
        tampering_detected
        and tampering_percentage >= config["tampering_percentage_threshold"]
        and visual_confidence < config["suspicious_threshold"]
    ):
        return "SIGNIFICANTLY_TAMPERED"
    if visual_confidence >= config["rendering_threshold"] and not tampering_detected:
        return "AUTHENTIC_WITH_RENDERING_DIFFERENCES"
    if visual_confidence >= config["suspicious_threshold"]:
        return "SUSPICIOUS"
    return "MODIFIED"


def _finite_psnr(value: float) -> float | None:
    return None if math.isinf(value) else float(value)


def authenticate_documents(
    original_pages: list[np.ndarray],
    verification_pages: list[np.ndarray],
    expected_hash: str | None,
    calculated_hash: str | None,
    weights: dict | None = None,
    tampering_threshold: int | None = None,
    minimum_region_area: int | None = None,
) -> dict:
    """
    Produce page-level and overall authentication results.

    The confidence score is the weighted mean of hash, SSIM, FFT, DCT, and
    edge scores. Hash matching is compared in constant time. A matching hash
    always returns AUTHENTIC because it proves identical canonical pixels;
    DSP analysis is still included as supporting telemetry.
    """
    if len(original_pages) != len(verification_pages):
        raise DSPProcessingError("Documents must have the same number of pages.")
    if not original_pages:
        raise DSPProcessingError("No pages were provided for authentication.")
    validated_weights = validate_authentication_weights(weights)
    config = get_authentication_config()
    hash_match = bool(
        expected_hash is not None
        and calculated_hash is not None
        and hmac.compare_digest(str(expected_hash).lower(), str(calculated_hash).lower())
    )
    hash_score = 100.0 if hash_match else 0.0
    page_results = []

    for page_number, (original, verification) in enumerate(
        zip(original_pages, verification_pages), start=1
    ):
        similarity = compare_images(original, verification)
        original_fft = extract_frequency_features(original)
        verification_fft = extract_frequency_features(verification)
        fft_score = compare_frequency_features(original_fft, verification_fft)
        original_dct = extract_dct_features(original)
        verification_dct = extract_dct_features(verification)
        dct_score = compare_dct_features(original_dct, verification_dct)
        original_features = extract_document_feature_vector(original)
        verification_features = extract_document_feature_vector(verification)
        edge_score = compare_edge_maps(
            original_features["edge_map"],
            verification_features["edge_map"],
        )
        localization = localize_tampering(
            original,
            verification,
            threshold=tampering_threshold,
            minimum_region_area=minimum_region_area,
        )
        tampering_percentage = _page_tampering_percentage(
            localization["outputs"]["tampering_mask"]
        )
        page_results.append({
            "page": page_number,
            "similarity": {
                "ssim": float(similarity["ssim"]),
                "mse": float(similarity["mse"]),
                "psnr": _finite_psnr(similarity["psnr"]),
            },
            "frequency": {
                "fft_similarity": fft_score,
                "dct_similarity": dct_score,
            },
            "edge": {"edge_similarity": edge_score},
            "tampering": {
                "detected": localization["region_count"] > 0,
                "tampering_percentage": tampering_percentage,
                "region_count": localization["region_count"],
                "regions": localization["regions"],
            },
        })

    overall_ssim = float(np.mean([page["similarity"]["ssim"] for page in page_results]))
    overall_fft = float(np.mean([
        page["frequency"]["fft_similarity"] for page in page_results
    ]))
    overall_dct = float(np.mean([
        page["frequency"]["dct_similarity"] for page in page_results
    ]))
    overall_edge = float(np.mean([
        page["edge"]["edge_similarity"] for page in page_results
    ]))
    overall_tampering_percentage = float(np.mean([
        page["tampering"]["tampering_percentage"] for page in page_results
    ]))
    confidence = float(np.clip(
        validated_weights["hash"] * hash_score
        + validated_weights["ssim"] * overall_ssim * 100.0
        + validated_weights["fft"] * overall_fft
        + validated_weights["dct"] * overall_dct
        + validated_weights["edge"] * overall_edge,
        0.0,
        100.0,
    ))
    visual_weights = {
        "ssim": validated_weights["ssim"],
        "fft": validated_weights["fft"],
        "dct": validated_weights["dct"],
        "edge": validated_weights["edge"],
    }
    visual_weight_total = sum(visual_weights.values())
    visual_confidence = float(np.clip(
        (
            visual_weights["ssim"] * overall_ssim * 100.0
            + visual_weights["fft"] * overall_fft
            + visual_weights["dct"] * overall_dct
            + visual_weights["edge"] * overall_edge
        ) / visual_weight_total,
        0.0,
        100.0,
    ))
    tampering_detected = any(page["tampering"]["detected"] for page in page_results)
    if hash_match:
        status = "AUTHENTIC"
    else:
        status = _status_for_hash_mismatch(
            visual_confidence,
            tampering_detected,
            overall_tampering_percentage,
            config,
        )

    return {
        "hash": {
            "expected": expected_hash,
            "calculated": calculated_hash,
            "match": hash_match,
            "status": "MATCH" if hash_match else "MISMATCH",
        },
        "similarity": {
            "ssim": overall_ssim,
            "mse": float(np.mean([page["similarity"]["mse"] for page in page_results])),
            "psnr": _finite_psnr(float(np.mean([
                page["similarity"]["psnr"] or 0.0 for page in page_results
            ]))),
        },
        "frequency": {
            "fft_similarity": overall_fft,
            "dct_similarity": overall_dct,
        },
        "edge": {"edge_similarity": overall_edge},
        "tampering": {
            "detected": tampering_detected,
            "tampering_percentage": overall_tampering_percentage,
            "modified_pages": [
                page["page"] for page in page_results if page["tampering"]["detected"]
            ],
            "total_region_count": sum(
                page["tampering"]["region_count"] for page in page_results
            ),
        },
        "confidence_score": confidence,
        "visual_confidence_score": visual_confidence,
        "status": status,
        "weights": validated_weights,
        "pages": page_results,
    }
