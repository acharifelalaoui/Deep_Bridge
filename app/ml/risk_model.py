"""
Modele de risque operatoire (Random Forest), inspire du travail du groupe precedent.

Donnees: data/dataset/deep-bridge-data-clean.csv
Cible: complication (0/1)
"""

from __future__ import annotations

import json
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from app.ml.clinical_dataset import (
    FEATURE_COLS,
    TARGET_COL,
    ClinicalPatient,
    load_clinical_dataframe,
)
from app.utils.paths import DATA_DIR, ensure_runtime_dirs

MODELS_DIR = DATA_DIR / "models"
DEFAULT_MODEL_PATH = MODELS_DIR / "risk_random_forest.pkl"
DEFAULT_METRICS_PATH = MODELS_DIR / "risk_random_forest_metrics.json"


@dataclass
class RiskPrediction:
    probability: float
    label: int
    message: str

    def display(self) -> str:
        pct = 100.0 * self.probability
        niveau = "eleve" if self.probability >= 0.5 else "modere" if self.probability >= 0.25 else "faible"
        return (
            f"Risque de complication: {pct:.1f}% ({niveau})\n"
            f"Classe predite: {self.label}\n"
            f"{self.message}"
        )


@dataclass
class TrainMetrics:
    n_samples: int
    n_train: int
    n_test: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    features: list[str]


def train_risk_model(
    csv_path: Path | None = None,
    model_path: Path | None = None,
) -> tuple[RandomForestClassifier, TrainMetrics]:
    ensure_runtime_dirs()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_clinical_dataframe(csv_path)
    x = df[FEATURE_COLS]
    y = df[TARGET_COL]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(x_train, y_train)
    y_pred = model.predict(x_test)
    y_proba = model.predict_proba(x_test)[:, 1]
    metrics = TrainMetrics(
        n_samples=len(df),
        n_train=len(x_train),
        n_test=len(x_test),
        accuracy=float(accuracy_score(y_test, y_pred)),
        precision=float(precision_score(y_test, y_pred, zero_division=0)),
        recall=float(recall_score(y_test, y_pred, zero_division=0)),
        f1=float(f1_score(y_test, y_pred, zero_division=0)),
        roc_auc=float(roc_auc_score(y_test, y_proba)),
        features=list(FEATURE_COLS),
    )
    out = Path(model_path or DEFAULT_MODEL_PATH)
    with out.open("wb") as f:
        pickle.dump({"model": model, "features": FEATURE_COLS}, f)
    DEFAULT_METRICS_PATH.write_text(
        json.dumps(asdict(metrics), indent=2), encoding="utf-8"
    )
    return model, metrics


def load_risk_model(model_path: Path | None = None) -> RandomForestClassifier:
    path = Path(model_path or DEFAULT_MODEL_PATH)
    if not path.exists():
        model, _ = train_risk_model()
        return model
    with path.open("rb") as f:
        bundle = pickle.load(f)
    return bundle["model"]


def predict_complication_risk(
    patient: ClinicalPatient,
    model: RandomForestClassifier | None = None,
) -> RiskPrediction:
    import pandas as pd

    clf = model or load_risk_model()
    x = pd.DataFrame([patient.feature_vector()], columns=FEATURE_COLS)
    proba = float(clf.predict_proba(x)[0, 1])
    label = int(clf.predict(x)[0])
    msg = (
        "Prediction basee sur le dataset clinique Deep Bridge "
        "(Random Forest, features pre-operatoires)."
    )
    return RiskPrediction(probability=proba, label=label, message=msg)
