"""Chargement du dataset clinique Deep Bridge (groupe precedent)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.utils.paths import DATA_DIR

DATASET_DIR = DATA_DIR / "dataset"
CLEAN_CSV = DATASET_DIR / "deep-bridge-data-clean.csv"

# Noms normalises utilises dans l'appli
FEATURE_COLS = [
    "age_arrondi",
    "sexe",          # 0 femme, 1 homme
    "s_plus",
    "technique",     # 1 patch, 2 eversion
    "shunt",
    "arterio",
    "re_inter",
    "anomalie",
    "anomalie_comm",
]
TARGET_COL = "complication"


@dataclass
class ClinicalPatient:
    patient_id: str
    age: int
    sexe: int
    s_plus: int
    technique: int
    shunt: int
    arterio: int
    re_inter: int
    anomalie: int
    anomalie_comm: int
    complication: int | None = None

    def feature_vector(self) -> list[float]:
        return [
            float(self.age),
            float(self.sexe),
            float(self.s_plus),
            float(self.technique),
            float(self.shunt),
            float(self.arterio),
            float(self.re_inter),
            float(self.anomalie),
            float(self.anomalie_comm),
        ]

    def display(self) -> str:
        sex = "H" if self.sexe == 1 else "F"
        comp = "?" if self.complication is None else str(self.complication)
        return f"#{self.patient_id} | {self.age} ans | {sex} | complication={comp}"


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for c in df.columns:
        cl = c.lower().strip()
        if "num" in cl:
            rename[c] = "patient_id"
        elif cl == "age_arrondi":
            rename[c] = "age_arrondi"
        elif cl == "age_calcul":
            rename[c] = "age_calcul"
        elif "femme" in cl or "homme" in cl:
            rename[c] = "sexe"
        elif cl in {"s+", "s_plus"}:
            rename[c] = "s_plus"
        elif "patch" in cl or "eversion" in cl:
            rename[c] = "technique"
        elif cl == "shunt":
            rename[c] = "shunt"
        elif cl == "arterio":
            rename[c] = "arterio"
        elif "re_inter" in cl or "re inter" in cl:
            rename[c] = "re_inter"
        elif cl == "anomalie":
            rename[c] = "anomalie"
        elif "anomalie_comm" in cl or "anomalie comm" in cl:
            rename[c] = "anomalie_comm"
        elif cl == "complication":
            rename[c] = "complication"
    out = df.rename(columns=rename).copy()
    return out


def load_clinical_dataframe(path: Path | None = None) -> pd.DataFrame:
    csv_path = Path(path or CLEAN_CSV)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Dataset clinique introuvable: {csv_path}. "
            "Copie deep-bridge-data-clean.csv dans data/dataset/"
        )
    df = pd.read_csv(csv_path)
    df = _normalize_columns(df)
    required = FEATURE_COLS + [TARGET_COL]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans le CSV: {missing}")
    df = df.dropna(subset=FEATURE_COLS + [TARGET_COL]).copy()
    df["patient_id"] = df.get("patient_id", range(1, len(df) + 1)).astype(str)
    df["age_arrondi"] = df["age_arrondi"].astype(int)
    for c in FEATURE_COLS[1:] + [TARGET_COL]:
        df[c] = df[c].astype(int)
    return df.reset_index(drop=True)


def dataframe_to_patients(df: pd.DataFrame) -> list[ClinicalPatient]:
    patients: list[ClinicalPatient] = []
    for _, row in df.iterrows():
        patients.append(
            ClinicalPatient(
                patient_id=str(row["patient_id"]),
                age=int(row["age_arrondi"]),
                sexe=int(row["sexe"]),
                s_plus=int(row["s_plus"]),
                technique=int(row["technique"]),
                shunt=int(row["shunt"]),
                arterio=int(row["arterio"]),
                re_inter=int(row["re_inter"]),
                anomalie=int(row["anomalie"]),
                anomalie_comm=int(row["anomalie_comm"]),
                complication=int(row["complication"]),
            )
        )
    return patients


def load_clinical_patients(path: Path | None = None) -> list[ClinicalPatient]:
    return dataframe_to_patients(load_clinical_dataframe(path))


def dataset_summary(path: Path | None = None) -> str:
    df = load_clinical_dataframe(path)
    n = len(df)
    n_comp = int(df[TARGET_COL].sum())
    return (
        f"Dataset clinique Deep Bridge: {n} patients, "
        f"{n_comp} avec complication ({100 * n_comp / n:.1f}%), "
        f"age moyen {df['age_arrondi'].mean():.1f} ans.\n"
        "Source: depot MBDS groupe2 tpi-python (CSV nettoye)."
    )
