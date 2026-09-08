"""Main application window."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.carotid.detection import ManualCarotidDetector, ROI, Side
from app.dicom.loader import DicomLoadError, load_dicom_folder
from app.dicom.series import DicomSeries
from app.imaging.filters import FilterType
from app.imaging.measurements import distance_mm
from app.report import (
    build_report,
    export_report_csv,
    export_report_json,
    export_report_pdf,
    export_report_txt,
)
from app.ui.analysis_panel import AnalysisPanel
from app.ui.measurement_panel import MeasurementPanel
from app.ui.patient_panel import PatientPanel
from app.ui.risk_panel import RiskPanel
from app.ui.series_panel import SeriesPanel
from app.ui.styles import DARK_STYLESHEET
from app.ui.viewer_widget import ToolMode, ViewerWidget
from app.utils.paths import DEMO_DIR, EXPORTS_DIR, ensure_runtime_dirs

logger = logging.getLogger("deep_bridge.ui")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Deep Bridge - Visualisation DICOM")
        self.resize(1400, 900)
        self.setStyleSheet(DARK_STYLESHEET)

        self.series_list: list[DicomSeries] = []
        self.current_series: DicomSeries | None = None
        self.slice_index = 0
        self.demo_mode = False
        self.detector = ManualCarotidDetector()

        self._build_ui()
        self._build_toolbar()
        self._build_statusbar()
        ensure_runtime_dirs()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        header = QHBoxLayout()
        title = QLabel("Deep Bridge")
        title.setObjectName("titleLabel")
        self.banner = QLabel("")
        self.banner.setObjectName("bannerLabel")
        self.banner.setVisible(False)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.banner, stretch=1)
        root.addLayout(header)

        disclaimer = QLabel(
            "Prototype universitaire - ne pas utiliser pour un diagnostic medical"
        )
        disclaimer.setObjectName("disclaimerLabel")
        disclaimer.setAlignment(Qt.AlignCenter)
        root.addWidget(disclaimer)

        splitter = QSplitter()
        left = QWidget()
        left_l = QVBoxLayout(left)
        self.series_panel = SeriesPanel()
        self.patient_panel = PatientPanel()
        left_l.addWidget(self.series_panel, stretch=2)
        left_l.addWidget(self.patient_panel, stretch=2)
        splitter.addWidget(left)

        center = QWidget()
        center_l = QVBoxLayout(center)
        self.viewer = ViewerWidget()
        center_l.addWidget(self.viewer, stretch=1)

        nav = QHBoxLayout()
        self.slice_label = QLabel("Slice: 0 / 0")
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setMinimum(0)
        self.slice_slider.setMaximum(0)
        self.slice_slider.valueChanged.connect(self._on_slice_changed)
        nav.addWidget(self.slice_label)
        nav.addWidget(self.slice_slider, stretch=1)
        center_l.addLayout(nav)

        controls = QHBoxLayout()
        self.wc_spin = QDoubleSpinBox()
        self.wc_spin.setRange(-2000, 4000)
        self.wc_spin.setValue(40)
        self.wc_spin.setPrefix("WC ")
        self.ww_spin = QDoubleSpinBox()
        self.ww_spin.setRange(1, 5000)
        self.ww_spin.setValue(400)
        self.ww_spin.setPrefix("WW ")
        self.wc_spin.valueChanged.connect(self._on_window_changed)
        self.ww_spin.valueChanged.connect(self._on_window_changed)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([f.value for f in FilterType])
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        btn_reset = QPushButton("Reset view")
        btn_reset.clicked.connect(self.viewer.reset_view)
        btn_pan = QPushButton("Pan")
        btn_pan.clicked.connect(lambda: self.viewer.set_tool(ToolMode.PAN))
        controls.addWidget(self.wc_spin)
        controls.addWidget(self.ww_spin)
        controls.addWidget(QLabel("Filter"))
        controls.addWidget(self.filter_combo)
        controls.addWidget(btn_pan)
        controls.addWidget(btn_reset)
        center_l.addLayout(controls)
        splitter.addWidget(center)

        self.measure_panel = MeasurementPanel()
        self.analysis_panel = AnalysisPanel()
        self.risk_panel = RiskPanel()
        right_tabs = QTabWidget()
        right_tabs.addTab(self.measure_panel, "Mesures")
        right_tabs.addTab(self.analysis_panel, "Pipeline")
        right_tabs.addTab(self.risk_panel, "Risk CSV")
        splitter.addWidget(right_tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 2)
        splitter.setSizes([240, 780, 380])
        root.addWidget(splitter, stretch=1)

        self.series_panel.series_selected.connect(self._on_series_selected)
        self.viewer.measure_completed.connect(self._on_measure)
        self.viewer.roi_completed.connect(self._on_roi)
        self.measure_panel.request_measure_tool.connect(
            lambda: self.viewer.set_tool(ToolMode.MEASURE)
        )
        self.measure_panel.request_roi_tool.connect(lambda: self.viewer.set_tool(ToolMode.ROI))
        self.measure_panel.stenosis_updated.connect(self._refresh_analysis_status)
        self.analysis_panel.pipeline_done.connect(self._refresh_analysis_status)
        self.analysis_panel.auto_rois.connect(self._on_auto_rois)
        self.risk_panel.risk_computed.connect(self._on_risk)
        self.risk_panel.patient_selected.connect(self._on_clinical_patient)

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        self.addToolBar(tb)
        act_open = QAction("Open DICOM Folder", self)
        act_open.setShortcut(QKeySequence.Open)
        act_open.triggered.connect(self.open_dicom_folder)
        act_demo = QAction("Demo", self)
        act_demo.triggered.connect(self.load_demo)
        act_export = QAction("Export report", self)
        act_export.triggered.connect(self.export_reports)
        act_shot = QAction("Screenshot", self)
        act_shot.triggered.connect(self.export_screenshot)
        tb.addAction(act_open)
        tb.addAction(act_demo)
        tb.addAction(act_export)
        tb.addAction(act_shot)

        # Also prominent buttons
        btn_bar = QWidget()
        hl = QHBoxLayout(btn_bar)
        hl.setContentsMargins(8, 0, 8, 0)
        b1 = QPushButton("Open DICOM")
        b1.clicked.connect(self.open_dicom_folder)
        b2 = QPushButton("Demo")
        b2.setObjectName("demoBtn")
        b2.clicked.connect(self.load_demo)
        b3 = QPushButton("Export")
        b3.clicked.connect(self.export_reports)
        hl.addWidget(b1)
        hl.addWidget(b2)
        hl.addWidget(b3)
        hl.addStretch()
        self.menuWidget()  # no-op safety
        tb.addWidget(btn_bar)

    def _build_statusbar(self) -> None:
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("Ready – load DICOM or DEMO")

    def set_demo_banner(self, enabled: bool) -> None:
        self.demo_mode = enabled
        self.banner.setVisible(enabled)
        if enabled:
            self.banner.setText("Mode DEMO - donnees synthetiques (pas un examen patient)")

    def open_dicom_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select DICOM folder")
        if not folder:
            return
        self._load_folder(Path(folder), demo=False)

    def load_demo(self) -> None:
        ensure_runtime_dirs()
        if not any(DEMO_DIR.rglob("*.dcm")):
            try:
                from app.utils.demo_data import generate_demo_series

                generate_demo_series(DEMO_DIR)
            except Exception as exc:  # noqa: BLE001
                QMessageBox.warning(
                    self,
                    "Demo data missing",
                    f"Could not generate demo data automatically:\n{exc}\n\n"
                    f"Run: python scripts/generate_demo_data.py",
                )
                return
        self._load_folder(DEMO_DIR, demo=True)

    def _load_folder(self, folder: Path, *, demo: bool) -> None:
        try:
            series_list = load_dicom_folder(folder)
        except DicomLoadError as exc:
            QMessageBox.critical(self, "DICOM load error", str(exc))
            return
        self.series_list = series_list
        self.set_demo_banner(demo or any(s.is_demo for s in series_list))
        self.series_panel.set_series(series_list)
        if series_list:
            self._on_series_selected(0)
            from PySide6.QtCore import QTimer

            QTimer.singleShot(100, self.viewer.refresh)
            QTimer.singleShot(300, self.viewer.refresh)
            sl0 = series_list[0].get_slice(0)
            self.statusBar().showMessage(
                f"Serie chargee: {series_list[0].num_slices} slices | "
                f"pixels {sl0.pixels.shape[0]}x{sl0.pixels.shape[1]} | "
                f"min={sl0.pixels.min():.0f} max={sl0.pixels.max():.0f}"
                + (" | DEMO" if self.demo_mode else "")
            )
        else:
            self.statusBar().showMessage("Aucune serie")

    def _on_series_selected(self, index: int) -> None:
        if index < 0 or index >= len(self.series_list):
            return
        self.current_series = self.series_list[index]
        n = self.current_series.num_slices
        self.slice_slider.blockSignals(True)
        self.slice_slider.setMaximum(max(0, n - 1))
        self.slice_slider.setValue(0)
        self.slice_slider.blockSignals(False)
        self.slice_index = 0
        wc, ww = self.current_series.default_window
        if wc is not None:
            self.wc_spin.blockSignals(True)
            self.wc_spin.setValue(wc)
            self.wc_spin.blockSignals(False)
        if ww is not None:
            self.ww_spin.blockSignals(True)
            self.ww_spin.setValue(max(ww, 1))
            self.ww_spin.blockSignals(False)
        self._show_current_slice(
            reset_window=wc is None or self.current_series.is_demo or self.demo_mode
        )

    def _on_slice_changed(self, value: int) -> None:
        self.slice_index = value
        self._show_current_slice()

    def _show_current_slice(self, *, reset_window: bool = False) -> None:
        series = self.current_series
        if series is None or series.num_slices == 0:
            self.viewer.clear()
            return
        sl = series.get_slice(self.slice_index)
        self.viewer.window_center = self.wc_spin.value()
        self.viewer.window_width = self.ww_spin.value()
        self.viewer.set_pixels(sl.pixels, reset_window=reset_window)
        if reset_window:
            self.wc_spin.blockSignals(True)
            self.ww_spin.blockSignals(True)
            self.wc_spin.setValue(self.viewer.window_center)
            self.ww_spin.setValue(self.viewer.window_width)
            self.wc_spin.blockSignals(False)
            self.ww_spin.blockSignals(False)
        self.slice_label.setText(f"Slice: {self.slice_index + 1} / {series.num_slices}")
        self.patient_panel.update_from_series(series, self.slice_index)
        meta = series.get_slice(self.slice_index).metadata
        self.analysis_panel.set_context(
            patient_id=meta.anonymized_patient_id,
            series_uid=series.series_instance_uid,
            slice_index=self.slice_index,
            is_demo=series.is_demo or self.demo_mode,
            series=series,
        )

    def _on_window_changed(self, *_args) -> None:
        self.viewer.set_window(self.wc_spin.value(), self.ww_spin.value())

    def _on_filter_changed(self, name: str) -> None:
        self.viewer.set_filter(name)
        self.viewer.show_preprocessed = name != FilterType.NONE.value

    def _on_measure(self, x1: float, y1: float, x2: float, y2: float) -> None:
        spacing = self.current_series.pixel_spacing if self.current_series else None
        result = distance_mm((x1, y1), (x2, y2), spacing)
        self.measure_panel.add_measurement(result.display())
        self.statusBar().showMessage(result.display())

    def _on_roi(self, x: int, y: int, w: int, h: int) -> None:
        roi = ROI(x, y, w, h, side=Side.UNKNOWN, label="manual")
        rois = list(self.detector.rois) + [roi]
        self.detector.set_rois(rois)
        self.measure_panel.add_measurement(f"ROI: x={x}, y={y}, w={w}, h={h}")
        if self.current_series is not None:
            meta = self.current_series.get_slice(self.slice_index).metadata
            self.analysis_panel.set_context(
                patient_id=meta.anonymized_patient_id,
                series_uid=self.current_series.series_instance_uid,
                slice_index=self.slice_index,
                is_demo=self.current_series.is_demo or self.demo_mode,
                roi=(x, y, w, h),
                series=self.current_series,
            )

    def _on_auto_rois(self, rois) -> None:
        # afficher les ROI detectees sur le viewer
        self.viewer._rois = [(r.x, r.y, r.width, r.height) for r in rois]
        self.detector.set_rois(list(rois))
        self.viewer.refresh()
        self.measure_panel.add_measurement(f"Detection auto: {len(rois)} ROI")

    def _on_risk(self, text: str) -> None:
        self.statusBar().showMessage("Risque operatoire calcule")
        # sync age into analysis panel if possible
        self.analysis_panel.age.setValue(self.risk_panel.age.value())

    def _on_clinical_patient(self, patient) -> None:
        self.analysis_panel.age.setValue(int(patient.age))
        self.statusBar().showMessage(f"Patient clinique selectionne: #{patient.patient_id}")

    def _refresh_analysis_status(self, text: str) -> None:
        self.statusBar().showMessage(text)

    def export_screenshot(self) -> None:
        ensure_runtime_dirs()
        path = EXPORTS_DIR / "screenshot.png"
        pix = self.viewer.image_label.grab()
        pix.save(str(path))
        self.statusBar().showMessage(f"Screenshot saved: {path}")

    def export_reports(self) -> None:
        report = build_report(
            self.current_series,
            measurements=list(self.measure_panel.history),
        )
        report.right_carotid = self.measure_panel.right_text
        report.left_carotid = self.measure_panel.left_text
        report.nascet = self.measure_panel.nascet_text
        report.ecst = self.measure_panel.ecst_text
        if self.analysis_panel.last_pipeline_text:
            report.pipeline_output = self.analysis_panel.last_pipeline_text
        if self.analysis_panel.last_recommendation:
            report.recommendation = self.analysis_panel.last_recommendation
        if getattr(self.risk_panel, "last_risk_text", ""):
            report.recommendation = (
                (report.recommendation + "\n\n" if report.recommendation else "")
                + self.risk_panel.last_risk_text
            )
        if self.demo_mode:
            report.is_demo = True
            report.status = "prototype / DEMO"
        paths = [
            export_report_json(report),
            export_report_txt(report),
            export_report_csv(report),
            export_report_pdf(report),
        ]
        msg = "Exported:\n" + "\n".join(str(p) for p in paths)
        QMessageBox.information(self, "Export complete", msg)
        self.statusBar().showMessage("Reports exported to exports/")
