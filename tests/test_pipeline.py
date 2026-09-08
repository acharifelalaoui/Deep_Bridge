"""Tests severite + recommandation + pipeline."""

from __future__ import annotations

import pytest

from app.carotid.pipeline import PipelineInput, run_empirical_pipeline
from app.carotid.recommendation import recommend_action
from app.carotid.severity import grade_nascet


def test_grade_thresholds():
    assert grade_nascet(20).grade == "mild"
    assert grade_nascet(55).grade == "moderate"
    assert grade_nascet(80).grade == "severe"
    assert grade_nascet(100).grade == "occlusion"


def test_recommendation_format():
    rec = recommend_action(100, 40, age=68)
    assert "droite" in rec.summary.lower() or "100" in rec.summary
    assert "40" in rec.summary
    assert "operation" in rec.action or "chirurgical" in rec.action or "intervention" in rec.action


def test_pipeline_direct_percent():
    out = run_empirical_pipeline(PipelineInput(pct_right=100, pct_left=40, age=70))
    assert out.right_pct == pytest.approx(100)
    assert out.left_pct == pytest.approx(40)
    assert out.recommendation is not None
    text = out.to_text()
    assert "100" in text and "40" in text


def test_pipeline_from_diameters():
    # Ds=2, Dref=5 => 60%
    out = run_empirical_pipeline(
        PipelineInput(d_stenosis_right=2, d_ref_right=5, d_stenosis_left=3, d_ref_left=5)
    )
    assert out.right_pct == pytest.approx(60)
    assert out.left_pct == pytest.approx(40)
