"""Geometric measurements using PixelSpacing when available."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class MeasurementResult:
    label: str
    value_px: float
    value_mm: float | None
    unit: str
    note: str = ""

    def display(self) -> str:
        if self.value_mm is not None:
            return f"{self.label}: {self.value_mm:.2f} {self.unit} ({self.value_px:.1f} px)"
        note = self.note or "physical unit unavailable (no PixelSpacing)"
        return f"{self.label}: {self.value_px:.1f} px — {note}"


def distance_px(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return float(np.hypot(p2[0] - p1[0], p2[1] - p1[1]))


def distance_mm(
    p1: tuple[float, float],
    p2: tuple[float, float],
    pixel_spacing: tuple[float, float] | None,
) -> MeasurementResult:
    """
    Euclidean distance.

    pixel_spacing is (row_spacing_mm, col_spacing_mm) as in DICOM PixelSpacing.
    Points are (x=col, y=row) in image coordinates.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    px = float(np.hypot(dx, dy))
    if pixel_spacing is None:
        return MeasurementResult(
            label="Distance",
            value_px=px,
            value_mm=None,
            unit="mm",
            note="PixelSpacing missing",
        )
    row_sp, col_sp = pixel_spacing
    mm = float(np.hypot(dx * col_sp, dy * row_sp))
    return MeasurementResult(label="Distance", value_px=px, value_mm=mm, unit="mm")


def diameter_mm(
    p1: tuple[float, float],
    p2: tuple[float, float],
    pixel_spacing: tuple[float, float] | None,
) -> MeasurementResult:
    result = distance_mm(p1, p2, pixel_spacing)
    result.label = "Diameter"
    return result


def polygon_area_px(points: list[tuple[float, float]]) -> float:
    if len(points) < 3:
        raise ValueError("At least 3 points required for area")
    xs = np.array([p[0] for p in points], dtype=np.float64)
    ys = np.array([p[1] for p in points], dtype=np.float64)
    return float(0.5 * np.abs(np.dot(xs, np.roll(ys, -1)) - np.dot(ys, np.roll(xs, -1))))


def polygon_area_mm2(
    points: list[tuple[float, float]],
    pixel_spacing: tuple[float, float] | None,
) -> MeasurementResult:
    area_px = polygon_area_px(points)
    if pixel_spacing is None:
        return MeasurementResult(
            label="Area",
            value_px=area_px,
            value_mm=None,
            unit="mm²",
            note="PixelSpacing missing",
        )
    row_sp, col_sp = pixel_spacing
    area_mm2 = area_px * row_sp * col_sp
    return MeasurementResult(
        label="Area",
        value_px=area_px,
        value_mm=area_mm2,
        unit="mm²",
    )