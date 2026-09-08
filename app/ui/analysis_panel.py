"""Panneau pipeline: bilaterale + age + annotation + sortie consignes."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.carotid.pipeline import PipelineInput, run_empirical_pipeline
from app.carotid.severity import grade_nascet
from app.dicom.series import DicomSeries
from app.ml.annotation_store import AnnotationStore, CarotidLabel


class AnalysisPanel(QWidget):
    pipeline_done = Signal(str)
    auto_rois = Signal(object)  # list[ROI]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.last_pipeline_text = ""
        self.last_recommendation = ""
        self._roi: tuple[int, int, int, int] | None = None
        self._series_uid = ""
        self._slice_index = 0
        self._is_demo = False
        self._patient_id = "anonyme"
        self._series: DicomSeries | None = None

        box = QGroupBox("Pipeline d'analyse (consignes)")
        form = QFormLayout(box)

        self.method = QComboBox()
        self.method.addItems(["NASCET", "ECST"])
        self.age = QSpinBox()
        self.age.setRange(0, 120)
        self.age.setSpecialValueText("age inconnu")
        self.age.setValue(0)

        self.ds_r = QDoubleSpinBox(); self._prep(self.ds_r)
        self.dr_r = QDoubleSpinBox(); self._prep(self.dr_r); self.dr_r.setValue(5.0)
        self.ds_l = QDoubleSpinBox(); self._prep(self.ds_l)
        self.dr_l = QDoubleSpinBox(); self._prep(self.dr_l); self.dr_l.setValue(5.0)

        self.use_pct = QComboBox()
        self.use_pct.addItems(["Depuis diametres", "Saisie directe des %"])
        self.pct_r = QDoubleSpinBox(); self.pct_r.setRange(0, 100); self.pct_r.setValue(60)
        self.pct_l = QDoubleSpinBox(); self.pct_l.setRange(0, 100); self.pct_l.setValue(40)

        form.addRow("Methode", self.method)
        form.addRow("Age patient", self.age)
        form.addRow("Mode", self.use_pct)
        form.addRow("D stenose droite", self.ds_r)
        form.addRow("D ref droite", self.dr_r)
        form.addRow("D stenose gauche", self.ds_l)
        form.addRow("D ref gauche", self.dr_l)
        form.addRow("% droite (direct)", self.pct_r)
        form.addRow("% gauche (direct)", self.pct_l)

        self.btn_run = QPushButton("Lancer le pipeline")
        self.btn_run.clicked.connect(self._run)
        self.btn_auto = QPushButton("Analyse auto de la serie chargee")
        self.btn_auto.clicked.connect(self._run_auto)
        form.addRow(self.btn_run)
        form.addRow(self.btn_auto)

        ann = QGroupBox("Etiquetage (pour IA supervisee)")
        aform = QFormLayout(ann)
        self.side = QComboBox(); self.side.addItems(["droite", "gauche", "inconnu"])
        self.ann_pct = QDoubleSpinBox(); self.ann_pct.setRange(0, 100); self.ann_pct.setValue(60)
        self.btn_save_label = QPushButton("Sauver label courant")
        self.btn_save_label.clicked.connect(self._save_label)
        aform.addRow("Cote", self.side)
        aform.addRow("% NASCET label", self.ann_pct)
        aform.addRow(self.btn_save_label)

        self.out = QTextEdit()
        self.out.setReadOnly(True)
        self.out.setPlaceholderText("La sortie du pipeline apparaitra ici...")

        note = QLabel(
            "Sortie au format des consignes (score + suggestion).\n"
            "Prototype pedagogique uniquement."
        )
        note.setObjectName("disclaimerLabel")
        note.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(box)
        layout.addWidget(ann)
        layout.addWidget(QLabel("Sortie"))
        layout.addWidget(self.out, stretch=1)
        layout.addWidget(note)

    @staticmethod
    def _prep(spin: QDoubleSpinBox) -> None:
        spin.setRange(0.0, 1000.0)
        spin.setDecimals(2)
        spin.setValue(2.0)
        spin.setSuffix(" mm")

    def set_context(
        self,
        *,
        patient_id: str,
        series_uid: str,
        slice_index: int,
        is_demo: bool,
        roi: tuple[int, int, int, int] | None = None,
        series: DicomSeries | None = None,
    ) -> None:
        self._patient_id = patient_id
        self._series_uid = series_uid
        self._slice_index = slice_index
        self._is_demo = is_demo
        if roi is not None:
            self._roi = roi
        if series is not None:
            self._series = series

    def _run_auto(self) -> None:
        if self._series is None:
            self.out.setPlainText("Charge d'abord une serie DICOM / DEMO.")
            return
        from app.carotid.end_to_end import analyze_series_empirical, overlay_candidates

        age = self.age.value() or None
        try:
            result = analyze_series_empirical(
                self._series, slice_index=None, age=age
            )
        except Exception as exc:  # noqa: BLE001
            self.out.setPlainText(f"Erreur analyse auto: {exc}")
            return
        text = result.to_text()
        self.last_pipeline_text = text
        self.last_recommendation = (
            result.pipeline.recommendation.display()
            if result.pipeline.recommendation
            else ""
        )
        self.out.setPlainText(text)
        rois = overlay_candidates(self._series.get_slice(self._slice_index).pixels, self._series, self._slice_index)
        self.auto_rois.emit(rois)
        self.pipeline_done.emit(text)

    def _run(self) -> None:
        age = self.age.value() or None
        if self.use_pct.currentIndex() == 1:
            data = PipelineInput(
                pct_right=self.pct_r.value(),
                pct_left=self.pct_l.value(),
                method=self.method.currentText(),
                age=age,
            )
        else:
            data = PipelineInput(
                d_stenosis_right=self.ds_r.value(),
                d_ref_right=self.dr_r.value(),
                d_stenosis_left=self.ds_l.value(),
                d_ref_left=self.dr_l.value(),
                method=self.method.currentText(),
                age=age,
            )
        result = run_empirical_pipeline(data)
        text = result.to_text()
        self.last_pipeline_text = text
        self.last_recommendation = (
            result.recommendation.display() if result.recommendation else ""
        )
        self.out.setPlainText(text)
        self.pipeline_done.emit(text)

    def _save_label(self) -> None:
        grade = grade_nascet(self.ann_pct.value()).grade
        label = CarotidLabel(
            patient_id_anon=self._patient_id,
            series_uid=self._series_uid or "unknown",
            slice_index=self._slice_index,
            side=self.side.currentText(),
            roi_xywh=self._roi,
            nascet_percent=self.ann_pct.value(),
            severity_grade=grade,
            is_demo=self._is_demo,
            notes="label manuel Deep Bridge",
        )
        store = AnnotationStore()
        store.add(label)
        path = store.save()
        self.out.append(f"\nLabel sauve dans {path} (grade={grade})")
