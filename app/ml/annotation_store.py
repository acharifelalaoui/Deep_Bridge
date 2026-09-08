"""Outil d'etiquetage pour preparer un apprentissage supervise."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.utils.paths import EXPORTS_DIR, ensure_runtime_dirs


@dataclass
class CarotidLabel:
    patient_id_anon: str
    series_uid: str
    slice_index: int
    side: str  # droite | gauche | inconnu
    roi_xywh: tuple[int, int, int, int] | None = None
    nascet_percent: float | None = None
    severity_grade: str | None = None
    notes: str = ""
    is_demo: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AnnotationStore:
    """Stocke des labels JSON pour un futur entrainement supervise."""

    def __init__(self, path: Path | None = None) -> None:
        ensure_runtime_dirs()
        self.path = path or (EXPORTS_DIR / "annotations.json")
        self.labels: list[CarotidLabel] = []
        if self.path.exists():
            self.load()

    def add(self, label: CarotidLabel) -> None:
        self.labels.append(label)

    def load(self) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.labels = []
        for item in data:
            if item.get("roi_xywh") is not None:
                item["roi_xywh"] = tuple(item["roi_xywh"])
            self.labels.append(CarotidLabel(**item))

    def save(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = []
        for lab in self.labels:
            d = asdict(lab)
            if d.get("roi_xywh") is not None:
                d["roi_xywh"] = list(d["roi_xywh"])
            payload.append(d)
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return self.path

    def count_by_grade(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for lab in self.labels:
            key = lab.severity_grade or "unknown"
            counts[key] = counts.get(key, 0) + 1
        return counts
