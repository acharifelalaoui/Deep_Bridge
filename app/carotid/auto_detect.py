"""Detection empirique simple (surtout utile sur DEMO / fantomes)."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from app.carotid.detection import DetectionResult, ROI, Side


@dataclass
class VesselCandidate:
    side: Side
    center_xy: tuple[int, int]
    radius_px: float
    roi: ROI


def _to_u8(image: np.ndarray) -> np.ndarray:
    img = image.astype(np.float64)
    lo, hi = np.percentile(img, [2, 98])
    if hi <= lo:
        hi = lo + 1.0
    norm = np.clip((img - lo) / (hi - lo), 0, 1)
    return (norm * 255).astype(np.uint8)


def detect_vessel_candidates(image: np.ndarray, max_vessels: int = 2) -> list[VesselCandidate]:
    """
    Procedure algorithmique simple:
    seuillage des zones claires + cercles (Hough) pour proposer des carotides.
    Concue pour les images DEMO; sur du vrai patient ca reste une aide, pas fiable.
    """
    u8 = _to_u8(image)
    blur = cv2.GaussianBlur(u8, (9, 9), 0)
    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=max(20, image.shape[1] // 8),
        param1=80,
        param2=25,
        minRadius=max(5, image.shape[0] // 40),
        maxRadius=max(20, image.shape[0] // 8),
    )
    candidates: list[VesselCandidate] = []
    if circles is None:
        return candidates

    rows, cols = image.shape[:2]
    mid = cols / 2.0
    circles = np.round(circles[0]).astype(int)
    # garder les plus gros / plus contrastes
    scored = []
    for x, y, r in circles:
        if x - r < 0 or y - r < 0 or x + r >= cols or y + r >= rows:
            continue
        patch = u8[y - r : y + r + 1, x - r : x + r + 1]
        scored.append((float(np.mean(patch)), int(x), int(y), int(r)))
    scored.sort(reverse=True)

    for _, x, y, r in scored[:max_vessels]:
        side = Side.LEFT if x >= mid else Side.RIGHT
        # convention image: gauche ecran ~ droite anatomique souvent inversee;
        # on reste coherents avec position image: x faible = droite ecran = "droite"
        side = Side.RIGHT if x < mid else Side.LEFT
        roi = ROI(x - r, y - r, 2 * r, 2 * r, side=side, label=f"auto-{side.value}")
        candidates.append(
            VesselCandidate(side=side, center_xy=(x, y), radius_px=float(r), roi=roi)
        )
    return candidates


class ExperimentalImageCarotidDetector:
    """Detection algorithmique empirique (DEMO / aide visuelle)."""

    def detect(self, image: np.ndarray) -> DetectionResult:
        cands = detect_vessel_candidates(image)
        rois = [c.roi for c in cands]
        if not rois:
            return DetectionResult(
                rois=[],
                method="hough_circles",
                message="Aucun vaisseau candidat detecte",
            )
        return DetectionResult(
            rois=rois,
            method="hough_circles",
            message=f"{len(rois)} candidat(s) detecte(s) (aide empirique)",
        )


def estimate_lumen_diameter_px(image: np.ndarray, cx: int, cy: int, search_r: int) -> float:
    """Estime le diametre de lumiere (zone claire) autour d'un centre."""
    u8 = _to_u8(image)
    rows, cols = u8.shape
    r = max(3, int(search_r))
    x0, x1 = max(0, cx - r), min(cols, cx + r + 1)
    y0, y1 = max(0, cy - r), min(rows, cy + r + 1)
    patch = u8[y0:y1, x0:x1]
    if patch.size == 0:
        return float(2 * search_r)
    # pixels "vaisseau" = intensite haute
    thr = max(120, int(np.percentile(patch, 70)))
    mask = patch >= thr
    if not np.any(mask):
        return float(2 * search_r)
    ys, xs = np.where(mask)
    # rayon moyen des pixels clairs par rapport au centre local
    lcx, lcy = cx - x0, cy - y0
    dist = np.sqrt((xs - lcx) ** 2 + (ys - lcy) ** 2)
    rad = float(np.percentile(dist, 80))
    return max(2.0, 2.0 * rad)


def estimate_diameter_mm(
    radius_px: float,
    pixel_spacing: tuple[float, float] | None,
) -> float | None:
    if pixel_spacing is None:
        return None
    sp = (pixel_spacing[0] + pixel_spacing[1]) / 2.0
    return float(radius_px * sp)  # radius_px ici = diametre en px si lumen est diametre

