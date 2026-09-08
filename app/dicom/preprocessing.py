"""Pixel conversion and optional image filters."""

from __future__ import annotations

import numpy as np

from app.dicom.metadata import ImageMetadata


def apply_rescale(pixels: np.ndarray, slope: float, intercept: float) -> np.ndarray:
    """Apply DICOM RescaleSlope / RescaleIntercept."""
    return pixels.astype(np.float64) * float(slope) + float(intercept)


def apply_photometric(pixels: np.ndarray, photometric: str) -> np.ndarray:
    """Invert MONOCHROME1 so higher values appear brighter for display pipelines."""
    if photometric.upper() == "MONOCHROME1":
        return pixels.max() - pixels
    return pixels


def pixels_from_dataset(ds, metadata: ImageMetadata | None = None) -> np.ndarray:
    """Convert PixelData to float array with rescale + photometric handling."""
    arr = ds.pixel_array.astype(np.float64)
    if metadata is None:
        from app.dicom.metadata import extract_metadata

        metadata = extract_metadata(ds)
    arr = apply_rescale(arr, metadata.rescale_slope, metadata.rescale_intercept)
    arr = apply_photometric(arr, metadata.photometric_interpretation)
    return arr


def normalize_01(pixels: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Min-max normalize to [0, 1]."""
    lo = float(np.min(pixels))
    hi = float(np.max(pixels))
    if hi - lo < eps:
        return np.zeros_like(pixels, dtype=np.float64)
    return (pixels - lo) / (hi - lo)


def gaussian_blur(pixels: np.ndarray, ksize: int = 3) -> np.ndarray:
    import cv2

    k = max(1, int(ksize) | 1)
    return cv2.GaussianBlur(pixels.astype(np.float32), (k, k), 0).astype(np.float64)


def median_filter(pixels: np.ndarray, ksize: int = 3) -> np.ndarray:
    import cv2

    k = max(1, int(ksize) | 1)
    # medianBlur needs uint8/16 for OpenCV; work on scaled buffer
    scaled = normalize_01(pixels)
    u8 = (scaled * 255).astype(np.uint8)
    out = cv2.medianBlur(u8, k)
    return out.astype(np.float64) / 255.0


def clahe_filter(pixels: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
    import cv2

    scaled = normalize_01(pixels)
    u8 = (scaled * 255).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    out = clahe.apply(u8)
    return out.astype(np.float64) / 255.0


def sharpen(pixels: np.ndarray) -> np.ndarray:
    import cv2

    scaled = normalize_01(pixels).astype(np.float32)
    blur = cv2.GaussianBlur(scaled, (0, 0), 1.0)
    return np.clip(scaled * 1.5 - blur * 0.5, 0, 1).astype(np.float64)