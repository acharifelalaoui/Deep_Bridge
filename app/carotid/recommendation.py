"""
Regles pedagogiques de suggestion d'action.

Important:
- Ce n'est PAS une aide a la decision clinique validee.
- Ca sert a produire une sortie du type demande dans les consignes du projet.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.carotid.severity import SeverityGrade, grade_nascet


@dataclass
class SideAssessment:
    side: str  # droite | gauche
    percentage: float | None
    grade: SeverityGrade | None = None

    def __post_init__(self) -> None:
        if self.percentage is not None and self.grade is None:
            self.grade = grade_nascet(self.percentage)


@dataclass
class RecommendationResult:
    summary: str
    action: str
    rationale: str
    right: SideAssessment | None = None
    left: SideAssessment | None = None
    age: int | None = None
    prototype_only: bool = True

    def display(self) -> str:
        lines = [self.summary, f"Suggestion: {self.action}", f"Motif: {self.rationale}"]
        if self.prototype_only:
            lines.append("Prototype pedagogique - ne pas utiliser en clinique.")
        return "\n".join(lines)


def recommend_action(
    right_pct: float | None,
    left_pct: float | None,
    age: int | None = None,
) -> RecommendationResult:
    """
    Heuristique simple pour la demo du pipeline:
    - occlusion / severe bilaterale ou unilaterale forte -> chirurgie evoquee
    - moderee -> discussion traitement medical / suivi
    - legere -> surveillance / ne rien faire d'invasif
    L'age module legerement le message (comme evoque dans les consignes).
    """
    right = SideAssessment("droite", right_pct) if right_pct is not None else None
    left = SideAssessment("gauche", left_pct) if left_pct is not None else None

    parts = []
    if right and right.percentage is not None:
        parts.append(f"carotide droite a {right.percentage:.0f}%")
    else:
        parts.append("carotide droite non evaluee")
    if left and left.percentage is not None:
        parts.append(f"carotide gauche a {left.percentage:.0f}%")
    else:
        parts.append("carotide gauche non evaluee")
    summary = "Le patient a la " + " et la ".join(parts) + "."

    scores = [s.percentage for s in (right, left) if s and s.percentage is not None]
    if not scores:
        return RecommendationResult(
            summary=summary,
            action="donnees insuffisantes",
            rationale="Aucun pourcentage NASCET saisi.",
            right=right,
            left=left,
            age=age,
        )

    max_pct = max(scores)
    max_grade = grade_nascet(max_pct)

    if max_pct >= 100 or max_grade.grade == "occlusion":
        action = "operation / revascularisation a discuter"
        rationale = "Presence d'une occlusion ou equivalent sur au moins un cote."
    elif max_pct >= 70:
        action = "intervention chirurgicale a discuter"
        rationale = "Stenose severe (>=70% NASCET) detectee sur au moins un cote."
        if age is not None and age >= 75:
            rationale += " Age eleve: peser soigneusement le rapport benefice/risque."
    elif max_pct >= 50:
        action = "traitement medicamenteux / suivi specialise"
        rationale = "Stenose moderee (50-69%)."
        if age is not None and age < 60:
            rationale += " Patient plus jeune: surveillance rapprochee possible."
    else:
        action = "ne rien faire d'invasif / surveillance"
        rationale = "Stenose legere (<50%) d'apres les valeurs saisies."

    return RecommendationResult(
        summary=summary,
        action=action,
        rationale=rationale,
        right=right,
        left=left,
        age=age,
    )
