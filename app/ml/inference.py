"""Inference: a brancher apres entrainement."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class InferenceResult:
    available: bool
    message: str
    outputs: dict | None = None


def run_inference(model, image: np.ndarray) -> InferenceResult:
    if model is None:
        return InferenceResult(available=False, message="Pas de modele charge")
    module = getattr(model, "module", model)
    if module is None:
        return InferenceResult(
            available=False,
            message=getattr(model, "message", "Modele indisponible"),
        )
    return InferenceResult(
        available=False,
        message="Modele non entraine: pas de prediction",
        outputs=None,
    )
