"""Segmentation: squelette pour plus tard."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class SegmentationResult:
    mask: np.ndarray | None
    method: str
    message: str = ""


class CarotidSegmenter(ABC):
    @abstractmethod
    def segment(self, image: np.ndarray) -> SegmentationResult:
        raise NotImplementedError


class ManualMaskSegmenter(CarotidSegmenter):
    def __init__(self, mask: np.ndarray | None = None) -> None:
        self.mask = mask

    def segment(self, image: np.ndarray) -> SegmentationResult:
        if self.mask is None:
            return SegmentationResult(mask=None, method="manual", message="Pas de masque")
        return SegmentationResult(mask=self.mask.astype(bool), method="manual")


class MLCarotidSegmenter(CarotidSegmenter):
    def __init__(self, checkpoint_path: str | None = None) -> None:
        self.checkpoint_path = checkpoint_path

    def segment(self, image: np.ndarray) -> SegmentationResult:
        return SegmentationResult(
            mask=None,
            method="ml",
            message="Segmentation auto non entrainee pour l'instant",
        )
