"""Panneau Risk Prediction (dataset clinique groupe precedent)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ml.clinical_dataset import (
    ClinicalPatient,
    dataset_summary,
    load_clinical_patients,
)
from app.ml.risk_model import load_risk_model, predict_complication_risk, train_risk_model


class RiskPanel(QWidget):
    patient_selected = Signal(object)  # ClinicalPatient
    risk_computed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.patients: list[ClinicalPatient] = []
        self.model = None
        self.last_risk_text = ""

        info = QLabel("Dataset clinique (CSV groupe DeepBridge precedent)")
        info.setWordWrap(True)

        self.summary = QLabel("Dataset non charge")
        self.summary.setWordWrap(True)

        self.list = QListWidget()
        self.list.setMaximumHeight(140)
        self.list.currentRowChanged.connect(self._on_select)

        btns = QHBoxLayout()
        self.btn_load = QPushButton("Charger dataset CSV")
        self.btn_train = QPushButton("Entrainer / recharger modele")
        self.btn_load.clicked.connect(self.load_dataset)
        self.btn_train.clicked.connect(self.train_model)
        btns.addWidget(self.btn_load)
        btns.addWidget(self.btn_train)

        form_box = QGroupBox("Saisie pre-operatoire (Risk Prediction)")
        form = QFormLayout(form_box)
        self.age = QSpinBox()
        self.age.setRange(18, 100)
        self.age.setValue(65)
        self.sexe = QComboBox()
        self.sexe.addItems(["Femme (0)", "Homme (1)"])
        self.s_plus = QComboBox()
        self.s_plus.addItems(["0", "1"])
        self.s_plus.setCurrentIndex(1)
        self.technique = QComboBox()
        self.technique.addItems(["Patch (1)", "Eversion (2)"])
        self.shunt = QComboBox()
        self.shunt.addItems(["Non (0)", "Oui (1)"])
        self.arterio = QComboBox()
        self.arterio.addItems(["0", "1"])
        self.re_inter = QComboBox()
        self.re_inter.addItems(["0", "1"])
        self.anomalie = QComboBox()
        self.anomalie.addItems(["0", "1"])
        self.anomalie_comm = QComboBox()
        self.anomalie_comm.addItems(["0", "1"])
        form.addRow("Age", self.age)
        form.addRow("Sexe", self.sexe)
        form.addRow("S+", self.s_plus)
        form.addRow("Technique", self.technique)
        form.addRow("Shunt", self.shunt)
        form.addRow("Arterio", self.arterio)
        form.addRow("Re-inter", self.re_inter)
        form.addRow("Anomalie", self.anomalie)
        form.addRow("Anomalie comm", self.anomalie_comm)

        self.btn_predict = QPushButton("Predire risque de complication")
        self.btn_predict.clicked.connect(self.predict)
        form.addRow(self.btn_predict)

        self.result_label = QLabel("Resultat: clique sur Predire")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet(
            "background:#2a2b31; border:1px solid #3a3b42; border-radius:6px; padding:8px;"
        )
        self.result_label.setMinimumHeight(70)
        form.addRow(self.result_label)

        self.out = QTextEdit()
        self.out.setReadOnly(True)
        self.out.setMaximumHeight(110)
        self.out.setPlaceholderText(
            "Details de la prediction (Random Forest) apparaîtront ici."
        )

        note = QLabel(
            "Modele inspire du travail tpi-python du groupe precedent.\n"
            "Prediction pedagogique / recherche, pas une decision clinique."
        )
        note.setObjectName("disclaimerLabel")
        note.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(self.summary)
        layout.addLayout(btns)
        layout.addWidget(QLabel("Patients du CSV"))
        layout.addWidget(self.list)
        layout.addWidget(form_box)
        layout.addWidget(self.out)
        layout.addWidget(note)
        layout.addStretch(1)

        try:
            self.load_dataset()
        except Exception as exc:  # noqa: BLE001
            self.summary.setText(f"Dataset non charge: {exc}")

        try:
            self.model = load_risk_model()
        except Exception:  # noqa: BLE001
            self.model = None

    def load_dataset(self) -> None:
        self.patients = load_clinical_patients()
        self.list.clear()
        for p in self.patients:
            self.list.addItem(p.display())
        self.summary.setText(dataset_summary())
        if self.patients:
            self.list.setCurrentRow(0)

    def train_model(self) -> None:
        try:
            _, metrics = train_risk_model()
            self.model = load_risk_model()
            text = (
                "Modele entraine sur le CSV clinique.\n"
                f"n={metrics.n_samples}\n"
                f"Accuracy={metrics.accuracy:.3f}\n"
                f"Precision={metrics.precision:.3f}\n"
                f"Recall={metrics.recall:.3f}\n"
                f"F1={metrics.f1:.3f}\n"
                f"ROC-AUC={metrics.roc_auc:.3f}\n"
            )
            self.out.setPlainText(text)
            self.result_label.setText("Modele pret. Clique Predire.")
        except Exception as exc:  # noqa: BLE001
            self.out.setPlainText(f"Erreur entrainement: {exc}")
            self.result_label.setText(f"Erreur: {exc}")

    def _on_select(self, row: int) -> None:
        if row < 0 or row >= len(self.patients):
            return
        p = self.patients[row]
        self.age.setValue(p.age)
        self.sexe.setCurrentIndex(1 if p.sexe == 1 else 0)
        self.s_plus.setCurrentIndex(1 if p.s_plus == 1 else 0)
        self.technique.setCurrentIndex(0 if p.technique == 1 else 1)
        self.shunt.setCurrentIndex(1 if p.shunt == 1 else 0)
        self.arterio.setCurrentIndex(1 if p.arterio == 1 else 0)
        self.re_inter.setCurrentIndex(1 if p.re_inter == 1 else 0)
        self.anomalie.setCurrentIndex(1 if p.anomalie == 1 else 0)
        self.anomalie_comm.setCurrentIndex(1 if p.anomalie_comm == 1 else 0)
        self.patient_selected.emit(p)

    def _patient_from_form(self) -> ClinicalPatient:
        return ClinicalPatient(
            patient_id="saisie",
            age=self.age.value(),
            sexe=self.sexe.currentIndex(),
            s_plus=int(self.s_plus.currentText()),
            technique=1 if self.technique.currentIndex() == 0 else 2,
            shunt=self.shunt.currentIndex(),
            arterio=int(self.arterio.currentText()),
            re_inter=int(self.re_inter.currentText()),
            anomalie=int(self.anomalie.currentText()),
            anomalie_comm=int(self.anomalie_comm.currentText()),
        )

    def predict(self) -> None:
        try:
            if self.model is None:
                self.result_label.setText("Chargement du modele...")
                self.model = load_risk_model()
            patient = self._patient_from_form()
            pred = predict_complication_risk(patient, self.model)
        except Exception as exc:  # noqa: BLE001
            msg = f"Erreur prediction: {exc}"
            self.out.setPlainText(msg)
            self.result_label.setText(msg)
            QMessageBox.warning(self, "Prediction", msg)
            return

        text = pred.display()
        row = self.list.currentRow()
        if 0 <= row < len(self.patients) and self.patients[row].complication is not None:
            truth = self.patients[row].complication
            text += f"\nVerite terrain (CSV): complication={truth}"

        self.last_risk_text = text
        self.out.setPlainText(text)
        short = text.split("\n")[0]
        self.result_label.setText(short)
        self.risk_computed.emit(text)
        QMessageBox.information(self, "Risque predit", text)
