"""Series list panel."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from app.dicom.series import DicomSeries


class SeriesPanel(QWidget):
    series_selected = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._series: list[DicomSeries] = []
        self.title = QLabel("Series")
        self.title.setObjectName("titleLabel")
        self.list = QListWidget()
        self.list.currentRowChanged.connect(self.series_selected.emit)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.list)

    def set_series(self, series_list: list[DicomSeries]) -> None:
        self._series = series_list
        self.list.clear()
        for s in series_list:
            item = QListWidgetItem(s.summary())
            if s.is_demo:
                item.setToolTip("DEMO DATA – NOT MEDICAL DATA")
            self.list.addItem(item)
        if series_list:
            self.list.setCurrentRow(0)

    def current_series(self) -> DicomSeries | None:
        row = self.list.currentRow()
        if row < 0 or row >= len(self._series):
            return None
        return self._series[row]
