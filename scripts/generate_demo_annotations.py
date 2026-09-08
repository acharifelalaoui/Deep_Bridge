#!/usr/bin/env python3
"""Cree quelques labels DEMO pour tester l'etiquetage / entrainement supervise."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.carotid.severity import grade_nascet
from app.ml.annotation_store import AnnotationStore, CarotidLabel
from app.utils.paths import EXPORTS_DIR, ensure_runtime_dirs


def main() -> None:
    ensure_runtime_dirs()
    store = AnnotationStore(EXPORTS_DIR / "annotations_demo.json")
    samples = [
        ("DEMO1", "droite", 20),
        ("DEMO1", "gauche", 35),
        ("DEMO2", "droite", 55),
        ("DEMO2", "gauche", 62),
        ("DEMO3", "droite", 75),
        ("DEMO3", "gauche", 48),
        ("DEMO4", "droite", 100),
        ("DEMO4", "gauche", 40),
        ("DEMO5", "droite", 15),
        ("DEMO5", "gauche", 80),
        ("DEMO6", "droite", 58),
        ("DEMO6", "gauche", 90),
    ]
    for i, (pid, side, pct) in enumerate(samples):
        store.add(
            CarotidLabel(
                patient_id_anon=pid,
                series_uid="demo-series",
                slice_index=i,
                side=side,
                nascet_percent=float(pct),
                severity_grade=grade_nascet(pct).grade,
                is_demo=True,
                notes="label synthetique DEMO",
            )
        )
    path = store.save()
    print(f"Labels DEMO ecrits: {path} ({len(store.labels)} labels)")


if __name__ == "__main__":
    main()
