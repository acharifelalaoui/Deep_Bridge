"""Windowing tests."""

from __future__ import annotations

import numpy as np
import pytest

from app.imaging.windowing import apply_window, default_window_from_data, to_display_uint8


def test_apply_window_range():
    pixels = np.linspace(0, 100, 50).reshape(5, 10)
    out = apply_window(pixels, center=50, width=100)
    assert out.min() >= 0.0
    assert out.max() <= 1.0


def test_invalid_width():
    with pytest.raises(ValueError):
        apply_window(np.zeros((4, 4)), center=0, width=0)


def test_default_window_and_uint8():
    pixels = np.arange(100, dtype=np.float64).reshape(10, 10)
    c, w = default_window_from_data(pixels)
    assert w > 0
    img = to_display_uint8(apply_window(pixels, c, w))
    assert img.dtype == np.uint8
    assert img.shape == (10, 10)
