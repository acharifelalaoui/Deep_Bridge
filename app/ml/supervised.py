"""
Classification supervisee de gravite (sklearn).

S'entraine sur des annotations JSON exportees depuis l'outil d'etiquetage.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.ml.annotation_store import AnnotationStore


@dataclass
class TrainReport:
    n_samples: int
    classes: list[str]
    accuracy: float | None
    message: str
    model_path: str | None = None


def _features_from_labels(store: AnnotationStore) -> tuple[np.ndarray, np.ndarray, list[str]]:
    xs: list[list[float]] = []
    ys: list[str] = []
    for lab in store.labels:
        if lab.nascet_percent is None or not lab.severity_grade:
            continue
        side = 1.0 if lab.side == "droite" else (0.0 if lab.side == "gauche" else 0.5)
        xs.append([float(lab.nascet_percent), side, float(lab.slice_index)])
        ys.append(lab.severity_grade)
    if not xs:
        raise ValueError("Pas assez de labels avec nascet_percent + severity_grade")
    classes = sorted(set(ys))
    y_idx = np.array([classes.index(v) for v in ys], dtype=np.int64)
    return np.asarray(xs, dtype=np.float64), y_idx, classes


def train_severity_classifier(
    annotations_path: Path,
    model_path: Path | None = None,
) -> TrainReport:
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    store = AnnotationStore(annotations_path)
    if annotations_path.exists() and not store.labels:
        store.load()
    x, y, classes = _features_from_labels(store)
    if len(x) < 8 or len(set(y.tolist())) < 2:
        return TrainReport(
            n_samples=len(x),
            classes=classes,
            accuracy=None,
            message="Pas assez de labels varies pour entrainer correctement.",
        )

    # stratify seulement si chaque classe a au moins 2 exemples
    counts = {c: int(np.sum(y == i)) for i, c in enumerate(classes)}
    can_stratify = min(counts.values()) >= 2 and len(x) >= 8
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y if can_stratify else None,
    )
    clf = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=500)),
        ]
    )
    clf.fit(x_train, y_train)
    acc = float(clf.score(x_test, y_test)) if len(x_test) else None
    out = model_path or (annotations_path.parent / "severity_classifier.pkl")
    with out.open("wb") as f:
        pickle.dump({"model": clf, "classes": classes}, f)
    return TrainReport(
        n_samples=len(x),
        classes=classes,
        accuracy=acc,
        message="Entrainement supervise termine sur les annotations fournies.",
        model_path=str(out),
    )


def predict_grade(model_path: Path, nascet_percent: float, side: str, slice_index: int = 0) -> str:
    with Path(model_path).open("rb") as f:
        bundle = pickle.load(f)
    clf = bundle["model"]
    classes: list[str] = bundle["classes"]
    side_v = 1.0 if side == "droite" else (0.0 if side == "gauche" else 0.5)
    pred = int(clf.predict([[nascet_percent, side_v, float(slice_index)]])[0])
    return classes[pred]
