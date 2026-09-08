"""Calculs NASCET / ECST a partir de diametres saisis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StenosisMethod(str, Enum):
    NASCET = "NASCET"
    ECST = "ECST"


@dataclass
class StenosisResult:
    method: StenosisMethod
    d_stenosis: float
    d_reference: float
    percentage: float
    message: str = "calcul indicatif"

    def display(self) -> str:
        return (
            f"{self.method.value}: {self.percentage:.1f}% "
            f"(Ds={self.d_stenosis:.2f}, Dref={self.d_reference:.2f})"
        )


def compute_nascet(d_stenosis: float, d_reference: float) -> StenosisResult:
    """% = 100 * (1 - Ds / Dref)."""
    if d_stenosis < 0 or d_reference <= 0:
        raise ValueError("D_stenose >= 0 et D_reference > 0 requis")
    pct = 100.0 * (1.0 - d_stenosis / d_reference)
    msg = "calcul indicatif"
    if d_stenosis > d_reference:
        msg = "attention: D_stenose > D_reference (verifier les mesures)"
    return StenosisResult(
        method=StenosisMethod.NASCET,
        d_stenosis=d_stenosis,
        d_reference=d_reference,
        percentage=pct,
        message=msg,
    )


def compute_ecst(d_stenosis: float, d_estimated_bulb: float) -> StenosisResult:
    """Meme forme de calcul, reference = bulbe estime saisi."""
    if d_stenosis < 0 or d_estimated_bulb <= 0:
        raise ValueError("D_stenose >= 0 et D_bulbe > 0 requis")
    pct = 100.0 * (1.0 - d_stenosis / d_estimated_bulb)
    return StenosisResult(
        method=StenosisMethod.ECST,
        d_stenosis=d_stenosis,
        d_reference=d_estimated_bulb,
        percentage=pct,
        message="calcul indicatif (ECST)",
    )


@dataclass
class BilateralStenosis:
    right: StenosisResult | None = None
    left: StenosisResult | None = None

    def summary_lines(self) -> list[str]:
        return [
            f"Carotide droite: {self.right.display() if self.right else 'non evalue'}",
            f"Carotide gauche: {self.left.display() if self.left else 'non evalue'}",
        ]
