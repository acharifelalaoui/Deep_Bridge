"""DICOM window/level operations."""

from __future__ import annotations

import numpy as np


def apply_window(
    pixels: np.ndarray,
    center: float,
    width: float,
) -> np.ndarray:
    """
    Apply windowing and return float image in [0, 1].

    Raises ValueError if width <= 0.
    """
    if width <= 0:
        raise ValueError("Window width must be > 0")
    lo = center - width / 2.0
    hi = center + width / 2.0
    clipped = np.clip(pixels.astype(np.float64), lo, hi)
    return (clipped - lo) / (hi - lo)


def default_window_from_data(pixels: np.ndarray) -> tuple[float, float]:
    """Heuristic window when DICOM WW/WC are missing."""
    p2, p98 = np.percentile(pixels, [2, 98])
    center = float((p2 + p98) / 2.0)
    width = float(max(p98 - p2, 1.0))
    return center, width


def to_display_uint8(windowed_01: np.ndarray) -> np.ndarray:
    """Convert [0,1] float to uint8 for Qt display."""
    return np.clip(windowed_01 * 255.0, 0, 255).astype(np.uint8)