"""Measurement geometry tests."""

from __future__ import annotations

import pytest

from app.imaging.measurements import distance_mm, distance_px, polygon_area_mm2


def test_distance_px():
    assert distance_px((0, 0), (3, 4)) == pytest.approx(5.0)


def test_distance_mm_with_spacing():
    result = distance_mm((0, 0), (10, 0), pixel_spacing=(0.5, 0.5))
    assert result.value_mm == pytest.approx(5.0)
    assert "mm" in result.display()


def test_distance_without_spacing():
    result = distance_mm((0, 0), (10, 0), pixel_spacing=None)
    assert result.value_mm is None
    assert "PixelSpacing" in result.display() or "unavailable" in result.display().lower() or "missing" in result.display().lower()


def test_area():
    pts = [(0, 0), (10, 0), (10, 10), (0, 10)]
    result = polygon_area_mm2(pts, (1.0, 1.0))
    assert result.value_mm == pytest.approx(100.0)
