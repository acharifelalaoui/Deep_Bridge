"""Patient / study technical info panel (anonymized)."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from app.dicom.series import DicomSeries


class PatientPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.title = QLabel("Study info")
        self.title.setObjectName("titleLabel")
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.text)

    def clear(self) -> None:
        self.text.setPlainText("No study loaded.")

    def update_from_series(self, series: DicomSeries | None, slice_index: int = 0) -> None:
        if series is None or series.num_slices == 0:
            self.clear()
            return
        sl = series.get_slice(max(0, min(slice_index, series.num_slices - 1)))
        meta = sl.metadata
        spacing = (
            f"{meta.pixel_spacing[0]:.4f} x {meta.pixel_spacing[1]:.4f} mm"
            if meta.pixel_spacing
            else "unavailable"
        )
        lines = [
            f"Patient ID: {meta.anonymized_patient_id}",
            f"DEMO: {'YES – NOT MEDICAL DATA' if series.is_demo else 'no'}",
            f"Modality: {meta.modality or 'n/a'}",
            f"Study UID: {meta.study_instance_uid or 'n/a'}",
            f"Series UID: {meta.series_instance_uid or 'n/a'}",
            f"Matrix: {meta.rows} x {meta.columns}",
            f"Slices: {series.num_slices}",
            f"Slice thickness: {meta.slice_thickness if meta.slice_thickness is not None else 'n/a'}",
            f"Pixel spacing: {spacing}",
            f"Window: C={meta.window_center} W={meta.window_width}",
            "",
            "Sensitive identifiers are masked.",
        ]
        self.text.setPlainText("\n".join(lines))
