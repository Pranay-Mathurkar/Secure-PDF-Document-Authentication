"""Independent DSP forensic pipeline using persisted reference pages."""
import math

import numpy as np

from app.services.dct_service import compare_dct_features, extract_dct_features
from app.services.feature_service import compare_edge_maps, extract_document_feature_vector
from app.services.fft_service import compare_frequency_features, extract_frequency_features
from app.services.preprocessing_service import DSPProcessingError, preprocess_image
from app.services.similarity_service import compare_images
from app.services.tamper_detection_service import localize_tampering


def analyze_dsp_pages(
    reference_pages: list[np.ndarray],
    candidate_pages: list[np.ndarray],
    threshold: int | None = None,
    minimum_region_area: int | None = None,
) -> dict:
    """Run only the DSP pipeline; no hash or QR functions are called."""
    if len(reference_pages) != len(candidate_pages):
        raise DSPProcessingError("Reference and candidate documents must have the same page count.")
    if not reference_pages:
        raise DSPProcessingError("No reference pages were provided for DSP analysis.")

    pages = []
    for page_number, (reference, candidate) in enumerate(
        zip(reference_pages, candidate_pages), start=1
    ):
        prepared_reference = preprocess_image(reference)
        prepared_candidate = preprocess_image(candidate)
        similarity = compare_images(
            prepared_reference,
            prepared_candidate,
            preprocess=False,
        )
        reference_fft = extract_frequency_features(prepared_reference, preprocess=False)
        candidate_fft = extract_frequency_features(prepared_candidate, preprocess=False)
        reference_dct = extract_dct_features(prepared_reference, preprocess=False)
        candidate_dct = extract_dct_features(prepared_candidate, preprocess=False)
        reference_features = extract_document_feature_vector(
            prepared_reference,
            preprocess=False,
        )
        candidate_features = extract_document_feature_vector(
            prepared_candidate,
            preprocess=False,
        )
        localization = localize_tampering(
            prepared_reference,
            prepared_candidate,
            threshold=threshold,
            minimum_region_area=minimum_region_area,
        )
        pages.append({
            "page": page_number,
            "similarity": {
                "ssim": float(similarity["ssim"]),
                "mse": float(similarity["mse"]),
                "psnr": None if math.isinf(similarity["psnr"]) else float(similarity["psnr"]),
            },
            "frequency": {
                "fft_similarity": compare_frequency_features(
                    reference_fft, candidate_fft
                ),
                "dct_similarity": compare_dct_features(
                    reference_dct, candidate_dct
                ),
            },
            "edge": {
                "edge_similarity": compare_edge_maps(
                    reference_features["edge_map"],
                    candidate_features["edge_map"],
                )
            },
            "tampering": {
                "detected": localization["region_count"] > 0,
                "tampering_percentage": float(
                    np.count_nonzero(localization["outputs"]["tampering_mask"])
                    * 100.0
                    / localization["outputs"]["tampering_mask"].size
                ),
                "region_count": localization["region_count"],
                "regions": localization["regions"],
            },
        })

    return {
        "pages": pages,
        "ssim": float(np.mean([page["similarity"]["ssim"] for page in pages])),
        "mse": float(np.mean([page["similarity"]["mse"] for page in pages])),
        "psnr": float(np.mean([
            page["similarity"]["psnr"] or 0.0 for page in pages
        ])),
        "fft_similarity": float(np.mean([
            page["frequency"]["fft_similarity"] for page in pages
        ])),
        "dct_similarity": float(np.mean([
            page["frequency"]["dct_similarity"] for page in pages
        ])),
        "edge_similarity": float(np.mean([
            page["edge"]["edge_similarity"] for page in pages
        ])),
        "tampering_detected": any(page["tampering"]["detected"] for page in pages),
        "tampering_percentage": float(np.mean([
            page["tampering"]["tampering_percentage"] for page in pages
        ])),
        "modified_pages": [
            page["page"] for page in pages if page["tampering"]["detected"]
        ],
        "modified_regions": sum(page["tampering"]["region_count"] for page in pages),
    }
