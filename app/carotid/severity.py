"""Grades de severite a partir d'un pourcentage NASCET."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SeverityGrade:
    percentage: float
    grade: str
    label_fr: str
    description: str

    def display(self) -> str:
        return f"{self.label_fr} ({self.grade}) - {self.percentage:.1f}%"


def grade_nascet(percentage: float) -> SeverityGrade:
    """
    Categories pedagogiques inspirees des seuils NASCET courants:
    - <50% : legere
    - 50-69% : moderee
    - 70-99% : severe
    - >=100% : occlusion
    """
    p = float(percentage)
    if p < 0:
        raise ValueError("Le pourcentage ne peut pas etre negatif")
    if p < 50:
        return SeverityGrade(p, "mild", "legere", "stenose < 50%")
    if p < 70:
        return SeverityGrade(p, "moderate", "moderee", "stenose 50-69%")
    if p < 100:
        return SeverityGrade(p, "severe", "severe", "stenose 70-99%")
    return SeverityGrade(p, "occlusion", "occlusion", "stenose >= 100% / occlusion")
