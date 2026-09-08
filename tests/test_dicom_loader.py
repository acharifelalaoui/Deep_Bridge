"""Unit tests for DICOM loader and slice ordering."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.dicom.loader import DicomLoadError, load_dicom_folder
from app.dicom.metadata import extract_metadata
from app.dicom.preprocessing import apply_rescale, normalize_01
from app.dicom.series import DicomSlice, sort_slices
from app.dicom.metadata import ImageMetadata


def test_sort_slices_by_instance_number():
    def mk(i: int, z: float) -> DicomSlice:
        meta = ImageMetadata(instance_number=i, image_position_patient=(0.0, 0.0, z))
        return DicomSlice(path=Path(f"f{i}.dcm"), metadata=meta, pixels=np.zeros((4, 4)))

    ordered = sort_slices([mk(3, 0), mk(1, 10), mk(2, 5)])
    assert [s.metadata.instance_number for s in ordered] == [1, 2, 3]


def test_apply_rescale():
    arr = np.array([[1.0, 2.0]], dtype=np.float64)
    out = apply_rescale(arr, slope=2.0, intercept=-1000)
    assert out[0, 0] == pytest.approx(-998)
    assert out[0, 1] == pytest.approx(-996)


def test_normalize_constant():
    arr = np.ones((8, 8))
    out = normalize_01(arr)
    assert np.allclose(out, 0.0)


def test_load_missing_folder():
    with pytest.raises(DicomLoadError):
        load_dicom_folder("/path/does/not/exist/deep_bridge_xyz")


def test_load_demo_if_present():
    demo = Path(__file__).resolve().parents[1] / "data" / "demo"
    if not any(demo.rglob("*.dcm")):
        pytest.skip("Demo DICOM not generated yet")
    series = load_dicom_folder(demo)
    assert len(series) >= 1
    assert series[0].num_slices >= 1
    assert series[0].is_demo is True
