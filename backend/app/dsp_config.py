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
})


def get_dsp_config() -> dict:
    """Return a mutable copy of the DSP configuration values."""
    return dict(DSP_CONFIG)
