"""Dataset helpers pour un futur entrainement."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class Annotation:
    patient_id_anon: str
    series_uid: str
    slice_index: int
    carotid_side: str
    roi_xywh: tuple[int, int, int, int] | None = None
    mask_path: str | None = None
    stenosis_percent_nascet: float | None = None
    stenosis_percent_ecst: float | None = None
    notes: str = ""


@dataclass
class PatientSplit:
    train: list[str] = field(default_factory=list)
    val: list[str] = field(default_factory=list)
    test: list[str] = field(default_factory=list)


def split_patients(
    patient_ids: list[str],
    ratios: tuple[float, float, float] = (0.7, 0.15, 0.15),
    seed: int = 42,
) -> PatientSplit:
    """Split par patient pour eviter le leakage entre slices."""
    if abs(sum(ratios) - 1.0) > 1e-6:
        raise ValueError("ratios must sum to 1")
    rng = np.random.default_rng(seed)
    ids = list(dict.fromkeys(patient_ids))
    rng.shuffle(ids)
    n = len(ids)
    n_train = int(n * ratios[0])
    n_val = int(n * ratios[1])
    return PatientSplit(
        train=ids[:n_train],
        val=ids[n_train : n_train + n_val],
        test=ids[n_train + n_val :],
    )


class CarotidDataset:
    def __init__(
        self,
        samples: list[tuple[np.ndarray, Annotation]],
        *,
        is_demo: bool = False,
    ) -> None:
        self.samples = samples
        self.is_demo = is_demo

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[np.ndarray, Annotation]:
        return self.samples[index]

    @staticmethod
    def required_fields_for_training() -> list[str]:
        return [
            "id patient anonymise",
            "reference serie/slice",
            "cote carotide",
            "ROI ou masque",
            "split train/val/test par patient",
        ]

    def export_manifest(self, path: Path) -> None:
        rows: list[dict[str, Any]] = []
        for _, ann in self.samples:
            rows.append(
                {
                    "patient_id_anon": ann.patient_id_anon,
                    "series_uid": ann.series_uid,
                    "slice_index": ann.slice_index,
                    "carotid_side": ann.carotid_side,
                    "is_demo": self.is_demo,
                }
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        import json

        path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
