"""Tests detection auto + analyse bout-en-bout."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.carotid.auto_detect import detect_vessel_candidates
from app.carotid.end_to_end import analyze_series_empirical
from app.dicom.loader import load_dicom_folder
from app.utils.demo_data import generate_demo_series
from app.utils.paths import DEMO_DIR


@pytest.fixture(scope="module")
def demo_series():
    if not any(Path(DEMO_DIR).rglob("*.dcm")):
        generate_demo_series(DEMO_DIR, n_slices=12)
    series_list = load_dicom_folder(DEMO_DIR)
    assert series_list
    return series_list[0]


def test_detect_candidates_on_demo(demo_series):
    img = demo_series.get_slice(demo_series.num_slices // 2).pixels
    cands = detect_vessel_candidates(img)
    # Sur DEMO on attend au moins 1 structure circulaire
    assert len(cands) >= 1


def test_end_to_end_demo(demo_series):
    result = analyze_series_empirical(demo_series, age=68)
    text = result.to_text()
    assert "Analyse auto" in text or "pipeline" in text.lower()
    assert result.pipeline is not None
