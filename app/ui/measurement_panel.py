"""Panneau mesures + calcul NASCET/ECST."""

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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.carotid.stenosis import compute_ecst, compute_nascet


class MeasurementPanel(QWidget):
    request_measure_tool = Signal()
    request_roi_tool = Signal()
    stenosis_updated = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.last_result_text = "non evalue"
        self.history: list[str] = []

        tools = QHBoxLayout()
        self.btn_measure = QPushButton("Mesurer distance")
        self.btn_roi = QPushButton("Dessiner ROI")
        self.btn_measure.clicked.connect(self.request_measure_tool.emit)
        self.btn_roi.clicked.connect(self.request_roi_tool.emit)
        tools.addWidget(self.btn_measure)
        tools.addWidget(self.btn_roi)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Les mesures apparaissent ici...")

        sten = QGroupBox("Calcul stenose")
        form = QFormLayout(sten)
        self.side = QComboBox()
        self.side.addItems(["Droite", "Gauche"])
        self.method = QComboBox()
        self.method.addItems(["NASCET", "ECST"])
        self.d_stenosis = QDoubleSpinBox()
        self.d_stenosis.setRange(0.0, 1000.0)
        self.d_stenosis.setDecimals(2)
        self.d_stenosis.setValue(2.0)
        self.d_stenosis.setSuffix(" mm")
        self.d_ref = QDoubleSpinBox()
        self.d_ref.setRange(0.01, 1000.0)
        self.d_ref.setDecimals(2)
        self.d_ref.setValue(5.0)
        self.d_ref.setSuffix(" mm")
        self.btn_calc = QPushButton("Calculer %")
        self.btn_calc.clicked.connect(self._compute)
        self.result_label = QLabel("Resultat: non evalue")
        self.result_label.setWordWrap(True)
        form.addRow("Cote", self.side)
        form.addRow("Methode", self.method)
        form.addRow("D stenose", self.d_stenosis)
        form.addRow("D reference", self.d_ref)
        form.addRow(self.btn_calc)
        form.addRow(self.result_label)

        note = QLabel(
            "Calcul indicatif a partir des diametres saisis.\n"
            "Ne pas considerer comme un diagnostic."
        )
        note.setObjectName("disclaimerLabel")
        note.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addLayout(tools)
        layout.addWidget(QLabel("Historique mesures"))
        layout.addWidget(self.log, stretch=1)
        layout.addWidget(sten)
        layout.addWidget(note)

        self.right_text = "non evalue"
        self.left_text = "non evalue"
        self.nascet_text = "non evalue"
        self.ecst_text = "non evalue"

    def add_measurement(self, text: str) -> None:
        self.history.append(text)
        self.log.append(text)

    def _compute(self) -> None:
        ds = self.d_stenosis.value()
        dr = self.d_ref.value()
        try:
            if self.method.currentText() == "NASCET":
                result = compute_nascet(ds, dr)
                self.nascet_text = result.display()
            else:
                result = compute_ecst(ds, dr)
                self.ecst_text = result.display()
        except ValueError as exc:
            self.result_label.setText(f"Erreur: {exc}")
            return
        side = self.side.currentText()
        text = f"{side}: {result.display()}"
        if side == "Droite":
            self.right_text = result.display()
        else:
            self.left_text = result.display()
        self.last_result_text = text
        self.result_label.setText(text)
        self.add_measurement(text)
        self.stenosis_updated.emit(text)
