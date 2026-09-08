"""Analyse bout-en-bout: DICOM/serie -> detection aide -> % -> suggestion."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.carotid.auto_detect import (
    detect_vessel_candidates,
    estimate_diameter_mm,
    estimate_lumen_diameter_px,
)
from app.carotid.detection import Side
from app.carotid.pipeline import PipelineInput, PipelineResult, run_empirical_pipeline
from app.dicom.series import DicomSeries


@dataclass
class AutoAnalysisResult:
    pipeline: PipelineResult
    details: list[str]

    def to_text(self) -> str:
        lines = ["Deep Bridge - Analyse auto (aide empirique)", ""]
        lines.extend(self.details)
        lines.append("")
        lines.append(self.pipeline.to_text())
        return "\n".join(lines)


def analyze_series_empirical(
    series: DicomSeries,
    slice_index: int | None = None,
    age: int | None = None,
) -> AutoAnalysisResult:
    """
    Pipeline empirique demontre sur une serie chargee:
    1) explore quelques coupes
    2) propose des carotides (cercles)
    3) estime des diametres
    4) calcule des % relatifs
    5) produit la sortie consignes
    """
    if series.num_slices == 0:
        raise ValueError("Serie vide")

    spacing = series.pixel_spacing
    details: list[str] = [f"DEMO: {'oui' if series.is_demo else 'non'}"]

    # Si slice imposee, on l'utilise; sinon on balaye pour trouver un max d'ecart
    if slice_index is not None:
        indices = [max(0, min(slice_index, series.num_slices - 1))]
    else:
        step = max(1, series.num_slices // 8)
        indices = list(range(0, series.num_slices, step))
        if (series.num_slices // 2) not in indices:
            indices.append(series.num_slices // 2)

    best = None  # (score, idx, right_d, left_d, n_cands)
    for idx in indices:
        img = series.get_slice(idx).pixels
        cands = detect_vessel_candidates(img, max_vessels=2)
        if len(cands) < 1:
            continue
        right = next((c for c in cands if c.side == Side.RIGHT), None)
        left = next((c for c in cands if c.side == Side.LEFT), None)
        if right is None:
            right = cands[0]
        if left is None and len(cands) > 1:
            left = cands[1]

        def diam(c):
            if c is None:
                return None
            # diametre lumen en pixels, plus sensible au retrecissement DEMO
            d_px = estimate_lumen_diameter_px(img, c.center_xy[0], c.center_xy[1], int(c.radius_px))
            mm = estimate_diameter_mm(d_px, spacing)
            if mm is not None:
                return mm
            return float(d_px * 0.5) if series.is_demo else None

        d_right, d_left = diam(right), diam(left)
        if d_right is None and d_left is None:
            continue
        vals = [v for v in (d_right, d_left) if v is not None]
        score = (max(vals) - min(vals)) if len(vals) == 2 else 0.0
        # prefer slices with 2 candidates and larger asymmetry (stenose relative)
        key = (len(vals), score)
        if best is None or key > (best[0], best[1]):
            best = (len(vals), score, idx, d_right, d_left, len(cands))

    if best is None:
        pipe = run_empirical_pipeline(PipelineInput(age=age))
        details.append("Echec detection: saisir les diametres manuellement.")
        return AutoAnalysisResult(pipeline=pipe, details=details)

    _, score, idx, d_right, d_left, n_cands = best
    details.extend(
        [
            f"Slice retenue: {idx + 1}/{series.num_slices}",
            f"Candidats detectes: {n_cands}",
            f"Diametre estime droite: {d_right}",
            f"Diametre estime gauche: {d_left}",
        ]
    )

    pct_right = None
    pct_left = None
    if d_right is not None and d_left is not None:
        dref = max(d_right, d_left)
        if dref > 0:
            pct_right = max(0.0, 100.0 * (1.0 - d_right / dref))
            pct_left = max(0.0, 100.0 * (1.0 - d_left / dref))
            details.append(
                "Approx pedagogique: % relatifs entre diametres detectes (pas un NASCET clinique)."
            )
    else:
        details.append("Un seul vaisseau detecte: % non calcule automatiquement.")

    pipe = run_empirical_pipeline(
        PipelineInput(pct_right=pct_right, pct_left=pct_left, age=age)
    )
    return AutoAnalysisResult(pipeline=pipe, details=details)


def overlay_candidates(image: np.ndarray, series: DicomSeries, slice_index: int) -> list:
    """Retourne les ROI detectees pour affichage."""
    sl = series.get_slice(slice_index)
    return [c.roi for c in detect_vessel_candidates(sl.pixels)]
