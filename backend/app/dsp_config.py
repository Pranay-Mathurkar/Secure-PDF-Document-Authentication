"""
Central configuration for future DSP and digital image processing services.
"""
from types import MappingProxyType

from app.config import settings


DSP_CONFIG = MappingProxyType({
    "image_resolution": settings.CANONICAL_DPI,
    "noise_reduction": None,
    "gaussian_kernel_size": 5,
    "median_filter_kernel_size": 3,
    "histogram_enhancement": None,
    "clahe_clip_limit": 2.0,
    "clahe_tile_grid_size": 8,
    "block_size": 64,
    "ssim_threshold": 0.95,
    "difference_threshold": 30,
    "tampering_threshold": 0.15,
    "minimum_region_area": 100,
    "fft_low_frequency_ratio": 0.10,
    "dct_low_frequency_ratio": 0.10,
    "dct_mid_frequency_ratio": 0.30,
    "canny_lower_threshold": 50,
    "canny_upper_threshold": 150,
    "tamper_morphology_kernel_size": 3,
    "tamper_morphology_iterations": 1,
    "tamper_alignment_max_shift": 10.0,
    "authentication_weights": {
        "hash": 0.40,
        "ssim": 0.25,
        "fft": 0.15,
        "dct": 0.10,
        "edge": 0.10,
    },
    "authentication_rendering_threshold": 90.0,
    "authentication_suspicious_threshold": 70.0,
    "authentication_significant_threshold": 45.0,
    "authentication_tampering_percentage_threshold": 5.0,
})


def get_dsp_config() -> dict:
    """Return a mutable copy of the DSP configuration values."""
    return dict(DSP_CONFIG)
