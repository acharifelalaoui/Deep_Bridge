"""Optional image filters."""

from __future__ import annotations

from enum import Enum

import numpy as np

from app.dicom.preprocessing import (
    clahe_filter,
    gaussian_blur,
    median_filter,
    sharpen,
)


class FilterType(str, Enum):
    NONE = "none"
    GAUSSIAN = "gaussian"
    MEDIAN = "median"
    CLAHE = "clahe"
    SHARPEN = "sharpen"


def apply_filter(pixels: np.ndarray, filter_type: FilterType | str) -> np.ndarray:
    kind = FilterType(filter_type) if isinstance(filter_type, str) else filter_type
    if kind == FilterType.NONE:
        return pixels
    if kind == FilterType.GAUSSIAN:
        return gaussian_blur(pixels)
    if kind == FilterType.MEDIAN:
        return median_filter(pixels)
    if kind == FilterType.CLAHE:
        return clahe_filter(pixels)
    if kind == FilterType.SHARPEN:
        return sharpen(pixels)
    raise ValueError(f"Unknown filter: {kind}")