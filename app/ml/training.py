"""Base pour un futur entrainement (pas encore utilise)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TrainConfig:
    epochs: int = 10
    batch_size: int = 4
    lr: float = 1e-3
    output_dir: Path = Path("checkpoints")
    is_demo: bool = False


class TrainingNotReadyError(RuntimeError):
    pass


def train_model(dataset, model, config: TrainConfig) -> dict:
    if dataset is None or len(dataset) == 0:
        raise TrainingNotReadyError("Dataset vide")
    raise TrainingNotReadyError(
        "Entrainement non lance: il manque le dataset annoté de l'universite."
    )


def validate_model(dataset, model) -> dict:
    raise TrainingNotReadyError("Pas de modele a valider pour le moment")


def save_checkpoint(model, path: Path) -> None:
    raise TrainingNotReadyError("Rien a sauvegarder: pas de poids entraines")
