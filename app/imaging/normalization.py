"""Normalization helpers (re-exported for clarity)."""

from __future__ import annotations

import numpy as np

from app.dicom.preprocessing import normalize_01

__all__ = ["normalize_01", "zscore"]


def zscore(pixels: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    mean = float(np.mean(pixels))
    std = float(np.std(pixels))
    if std < eps:
        return np.zeros_like(pixels, dtype=np.float64)
    return (pixels - mean) / std