"""Specs / petits modeles de test (non entraines sur donnees medicales)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelSpec:
    name: str
    task: str
    input_channels: int = 1
    notes: str = ""


class SimpleSegmentationSpec(ModelSpec):
    def __init__(self) -> None:
        super().__init__(name="UNetPlaceholder", task="segmentation", notes="a implementer")


class SimpleClassifierSpec(ModelSpec):
    def __init__(self) -> None:
        super().__init__(
            name="StenosisClassifierPlaceholder",
            task="classification",
            notes="a implementer apres annotations",
        )


def try_import_torch():
    try:
        import torch
        import torch.nn as nn

        return torch, nn
    except ImportError:
        return None, None


class TinyDemoCNN:
    """Petit CNN pour tester l'import torch, pas entraine."""

    def __init__(self, num_classes: int = 2) -> None:
        torch, nn = try_import_torch()
        if torch is None:
            self.module = None
            self.message = "torch non installe"
            return

        class _Net(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.features = nn.Sequential(
                    nn.Conv2d(1, 8, 3, padding=1),
                    nn.ReLU(),
                    nn.AdaptiveAvgPool2d((1, 1)),
                )
                self.head = nn.Linear(8, num_classes)

            def forward(self, x):  # type: ignore[no-untyped-def]
                x = self.features(x)
                x = x.view(x.size(0), -1)
                return self.head(x)

        self.module = _Net()
        self.message = "CNN non entraine"
