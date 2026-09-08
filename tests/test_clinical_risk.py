"""Tests dataset clinique + modele de risque."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ml.clinical_dataset import load_clinical_dataframe, load_clinical_patients
from app.ml.risk_model import predict_complication_risk, train_risk_model

CSV = Path(__file__).resolve().parents[1] / "data" / "dataset" / "deep-bridge-data-clean.csv"


@pytest.mark.skipif(not CSV.exists(), reason="CSV clinique absent")
def test_load_clinical_csv():
    df = load_clinical_dataframe(CSV)
    assert len(df) > 100
    assert "complication" in df.columns
    patients = load_clinical_patients(CSV)
    assert len(patients) == len(df)


@pytest.mark.skipif(not CSV.exists(), reason="CSV clinique absent")
def test_train_and_predict_risk(tmp_path):
    model_path = tmp_path / "risk.pkl"
    model, metrics = train_risk_model(CSV, model_path)
    assert metrics.n_samples > 100
    assert 0.0 <= metrics.roc_auc <= 1.0
    patients = load_clinical_patients(CSV)
    pred = predict_complication_risk(patients[0], model)
    assert 0.0 <= pred.probability <= 1.0
    assert pred.label in (0, 1)
