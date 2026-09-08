"""Detection carotide: ROI manuelle + stubs pour plus tard."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import numpy as np


class Side(str, Enum):
    RIGHT = "right"
    LEFT = "left"
    UNKNOWN = "unknown"


@dataclass
class ROI:
    x: int
    y: int
    width: int
    height: int
    side: Side = Side.UNKNOWN
    label: str = "ROI"

    def as_slice(self) -> tuple[slice, slice]:
        return slice(self.y, self.y + self.height), slice(self.x, self.x + self.width)

    def clip_to(self, rows: int, cols: int) -> "ROI":
        x0 = max(0, min(self.x, cols - 1))
        y0 = max(0, min(self.y, rows - 1))
        x1 = max(x0 + 1, min(self.x + self.width, cols))
        y1 = max(y0 + 1, min(self.y + self.height, rows))
        return ROI(x0, y0, x1 - x0, y1 - y0, self.side, self.label)


@dataclass
class DetectionResult:
    rois: list[ROI]
    method: str
    message: str = ""


class CarotidDetector(ABC):
    @abstractmethod
    def detect(self, image: np.ndarray) -> DetectionResult:
        raise NotImplementedError


class ManualCarotidDetector(CarotidDetector):
    """ROI dessinee par l'utilisateur."""

    def __init__(self, rois: list[ROI] | None = None) -> None:
        self.rois = rois or []

    def set_rois(self, rois: list[ROI]) -> None:
        self.rois = rois

    def detect(self, image: np.ndarray) -> DetectionResult:
        rows, cols = image.shape[:2]
        clipped = [r.clip_to(rows, cols) for r in self.rois]
        return DetectionResult(rois=clipped, method="manual", message="ROI manuelle")


class ExperimentalImageCarotidDetector(CarotidDetector):
    """Detection algorithmique empirique (Hough) - surtout utile en DEMO."""

    def detect(self, image: np.ndarray) -> DetectionResult:
        from app.carotid.auto_detect import detect_vessel_candidates

        cands = detect_vessel_candidates(image)
        rois = [c.roi for c in cands]
        return DetectionResult(
            rois=rois,
            method="hough_circles",
            message=(
                f"{len(rois)} candidat(s)"
                if rois
                else "Aucun candidat - passer en ROI manuelle"
            ),
        )


class MLCarotidDetector(CarotidDetector):
    """A brancher plus tard quand un modele sera entraine."""

    def __init__(self, checkpoint_path: str | None = None) -> None:
        self.checkpoint_path = checkpoint_path
        self._model = None

    def load(self) -> None:
        raise FileNotFoundError(
            "Pas de modele entraine pour le moment (dataset annoté requis)."
        )

    def detect(self, image: np.ndarray) -> DetectionResult:
        return DetectionResult(
            rois=[],
            method="ml",
            message="Modele non charge",
        )
