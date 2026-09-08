"""Pipeline empirique: mesures -> NASCET -> grade -> suggestion."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.carotid.recommendation import RecommendationResult, recommend_action
from app.carotid.severity import SeverityGrade, grade_nascet
from app.carotid.stenosis import StenosisResult, compute_ecst, compute_nascet


@dataclass
class PipelineInput:
    d_stenosis_right: float | None = None
    d_ref_right: float | None = None
    d_stenosis_left: float | None = None
    d_ref_left: float | None = None
    method: str = "NASCET"
    age: int | None = None
    # si les % sont deja connus (saisie directe)
    pct_right: float | None = None
    pct_left: float | None = None


@dataclass
class PipelineResult:
    right_pct: float | None = None
    left_pct: float | None = None
    right_grade: SeverityGrade | None = None
    left_grade: SeverityGrade | None = None
    right_stenosis: StenosisResult | None = None
    left_stenosis: StenosisResult | None = None
    recommendation: RecommendationResult | None = None
    notes: list[str] = field(default_factory=list)

    def to_text(self) -> str:
        lines = ["Deep Bridge - Sortie pipeline", ""]
        if self.right_pct is not None:
            g = self.right_grade.display() if self.right_grade else ""
            lines.append(f"Carotide droite: {self.right_pct:.1f}% | {g}")
        else:
            lines.append("Carotide droite: non evaluee")
        if self.left_pct is not None:
            g = self.left_grade.display() if self.left_grade else ""
            lines.append(f"Carotide gauche: {self.left_pct:.1f}% | {g}")
        else:
            lines.append("Carotide gauche: non evaluee")
        lines.append("")
        if self.recommendation:
            lines.append(self.recommendation.display())
        if self.notes:
            lines.append("")
            lines.extend(self.notes)
        return "\n".join(lines)


def _compute_side(
    d_stenosis: float | None,
    d_ref: float | None,
    pct: float | None,
    method: str,
) -> tuple[float | None, StenosisResult | None]:
    if pct is not None:
        return float(pct), None
    if d_stenosis is None or d_ref is None:
        return None, None
    if method.upper() == "ECST":
        res = compute_ecst(d_stenosis, d_ref)
    else:
        res = compute_nascet(d_stenosis, d_ref)
    return res.percentage, res


def run_empirical_pipeline(data: PipelineInput) -> PipelineResult:
    right_pct, right_res = _compute_side(
        data.d_stenosis_right, data.d_ref_right, data.pct_right, data.method
    )
    left_pct, left_res = _compute_side(
        data.d_stenosis_left, data.d_ref_left, data.pct_left, data.method
    )

    result = PipelineResult(
        right_pct=right_pct,
        left_pct=left_pct,
        right_stenosis=right_res,
        left_stenosis=left_res,
        right_grade=grade_nascet(right_pct) if right_pct is not None else None,
        left_grade=grade_nascet(left_pct) if left_pct is not None else None,
        recommendation=recommend_action(right_pct, left_pct, age=data.age),
        notes=[
            "Approche empirique des consignes: visualisation -> mesures -> NASCET/ECST -> sortie.",
            "Suggestion d'action = regles pedagogiques du prototype uniquement.",
        ],
    )
    return result
