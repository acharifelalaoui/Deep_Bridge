"""Generation d'un rapport d'analyse simple."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.carotid.stenosis import BilateralStenosis, StenosisResult
from app.dicom.series import DicomSeries
from app.utils.paths import EXPORTS_DIR, ensure_runtime_dirs


@dataclass
class AnalysisReport:
    title: str = "Deep Bridge - Rapport"
    patient_id: str = "anonyme/demo"
    study_uid: str = ""
    series_uid: str = ""
    modality: str = ""
    num_slices: int = 0
    pixel_spacing: str = "inconnu"
    right_carotid: str = "non evalue"
    left_carotid: str = "non evalue"
    nascet: str = "non evalue"
    ecst: str = "non evalue"
    pipeline_output: str = ""
    recommendation: str = ""
    measurements: list[str] = field(default_factory=list)
    status: str = "prototype"
    is_demo: bool = False
    disclaimer: str = (
        "Prototype universitaire. Resultats indicatifs, pas un diagnostic."
    )
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_text(self) -> str:
        lines = [
            self.title,
            "=" * len(self.title),
            f"Patient ID: {self.patient_id}",
            f"Study: {self.study_uid or 'n/a'}",
            f"Series: {self.series_uid or 'n/a'}",
            f"Modality: {self.modality or 'n/a'}",
            "",
            "Image:",
            f"  - Nombre de slices: {self.num_slices}",
            f"  - Pixel spacing: {self.pixel_spacing}",
            "",
            "Carotides:",
            f"  - Droite: {self.right_carotid}",
            f"  - Gauche: {self.left_carotid}",
            "",
            "Stenose:",
            f"  - NASCET: {self.nascet}",
            f"  - ECST: {self.ecst}",
            "",
            "Pipeline / suggestion:",
            self.pipeline_output or "  - non lance",
            "",
            "Mesures:",
        ]
        if self.measurements:
            lines.extend(f"  - {m}" for m in self.measurements)
        else:
            lines.append("  - aucune")
        lines.extend(
            [
                "",
                f"Statut: {self.status}" + (" / DEMO" if self.is_demo else ""),
                "",
                self.disclaimer,
            ]
        )
        if self.is_demo:
            lines.append("Donnees DEMO (synthetiques)")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return asdict(self)


def build_report(
    series: DicomSeries | None,
    bilateral: BilateralStenosis | None = None,
    measurements: list[str] | None = None,
    nascet: StenosisResult | None = None,
    ecst: StenosisResult | None = None,
) -> AnalysisReport:
    report = AnalysisReport()
    if series is not None:
        report.study_uid = series.study_instance_uid
        report.series_uid = series.series_instance_uid
        report.modality = series.modality
        report.num_slices = series.num_slices
        report.is_demo = series.is_demo
        report.patient_id = "DEMO" if series.is_demo else "anonyme"
        spacing = series.pixel_spacing
        report.pixel_spacing = (
            f"{spacing[0]:.4f} x {spacing[1]:.4f} mm" if spacing else "indisponible"
        )
        if series.is_demo:
            report.status = "prototype / DEMO"
    if bilateral is not None:
        report.right_carotid = (
            bilateral.right.display() if bilateral.right else "non evalue"
        )
        report.left_carotid = (
            bilateral.left.display() if bilateral.left else "non evalue"
        )
    if nascet is not None:
        report.nascet = nascet.display()
    if ecst is not None:
        report.ecst = ecst.display()
    if measurements:
        report.measurements = list(measurements)
    return report


def export_report_json(report: AnalysisReport, path: Path | None = None) -> Path:
    ensure_runtime_dirs()
    out = path or (EXPORTS_DIR / f"rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def export_report_txt(report: AnalysisReport, path: Path | None = None) -> Path:
    ensure_runtime_dirs()
    out = path or (EXPORTS_DIR / f"rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report.to_text(), encoding="utf-8")
    return out


def export_report_csv(report: AnalysisReport, path: Path | None = None) -> Path:
    ensure_runtime_dirs()
    out = path or (EXPORTS_DIR / f"rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    rows = [
        ("patient_id", report.patient_id),
        ("study_uid", report.study_uid),
        ("series_uid", report.series_uid),
        ("num_slices", str(report.num_slices)),
        ("pixel_spacing", report.pixel_spacing),
        ("right_carotid", report.right_carotid),
        ("left_carotid", report.left_carotid),
        ("nascet", report.nascet),
        ("ecst", report.ecst),
        ("status", report.status),
        ("is_demo", str(report.is_demo)),
    ]
    lines = ["key,value"]
    for k, v in rows:
        safe = v.replace('"', "'")
        lines.append(f'{k},"{safe}"')
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def export_report_pdf(report: AnalysisReport, path: Path | None = None) -> Path:
    ensure_runtime_dirs()
    out = path or (EXPORTS_DIR / f"rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        return export_report_txt(report, out.with_suffix(".txt"))

    c = canvas.Canvas(str(out), pagesize=A4)
    width, height = A4
    y = height - 50
    for line in report.to_text().splitlines():
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(40, y, line[:110])
        y -= 14
    c.save()
    return out
