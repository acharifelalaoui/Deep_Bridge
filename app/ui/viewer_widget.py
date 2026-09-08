"""Viewer DICOM — rendu direct (évite le bug QLabel+stylesheet sous Windows)."""

from __future__ import annotations

from enum import Enum, auto

import numpy as np
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.imaging.filters import FilterType, apply_filter
from app.imaging.windowing import apply_window, default_window_from_data, to_display_uint8


class ToolMode(Enum):
    NONE = auto()
    MEASURE = auto()
    ROI = auto()
    PAN = auto()


class ViewerWidget(QWidget):
    measure_completed = Signal(float, float, float, float)
    roi_completed = Signal(int, int, int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("dicomViewer")
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(320, 320)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self._pixels: np.ndarray | None = None
        self._display: np.ndarray | None = None
        self._rgb: np.ndarray | None = None
        self._source_pix: QPixmap | None = None
        self._canvas: QPixmap | None = None
        self._error: str | None = None
        self._placeholder = "Ouvrir un dossier DICOM ou charger la DEMO"

        self.window_center = 40.0
        self.window_width = 400.0
        self.filter_type = FilterType.NONE
        self.show_preprocessed = False
        self.zoom = 1.0
        self.offset = QPointF(0, 0)
        self.tool = ToolMode.NONE
        self._drag_origin: QPoint | None = None
        self._img_origin: tuple[float, float] | None = None
        self._temp_end: tuple[float, float] | None = None
        self._rois: list[tuple[int, int, int, int]] = []
        self._measure_lines: list[tuple[tuple[float, float], tuple[float, float]]] = []
        self._last_scaled_rect = QRectF()
        self._last_image_size = (1, 1)

        # Compat pour export_screenshot / ancien code
        self.image_label = self

    def set_pixels(self, pixels: np.ndarray, *, reset_window: bool = False) -> None:
        if pixels is None or pixels.size == 0:
            self.clear()
            return
        self._pixels = np.asarray(pixels, dtype=np.float64)
        self._error = None
        if reset_window:
            self.window_center, self.window_width = default_window_from_data(self._pixels)
        self._rois.clear()
        self._measure_lines.clear()
        self.zoom = 1.0
        self.offset = QPointF(0, 0)
        self.refresh()

    def clear(self) -> None:
        self._pixels = None
        self._display = None
        self._rgb = None
        self._source_pix = None
        self._canvas = None
        self._error = None
        self.update()

    def reset_view(self) -> None:
        self.zoom = 1.0
        self.offset = QPointF(0, 0)
        if self._pixels is not None:
            self.window_center, self.window_width = default_window_from_data(self._pixels)
        self.refresh()

    def set_window(self, center: float, width: float) -> None:
        self.window_center = float(center)
        self.window_width = max(float(width), 1.0)
        self.refresh()

    def set_filter(self, filter_type: FilterType | str) -> None:
        self.filter_type = FilterType(filter_type) if isinstance(filter_type, str) else filter_type
        self.refresh()

    def set_tool(self, tool: ToolMode) -> None:
        self.tool = tool

    def pixmap(self):  # noqa: ANN201 — compat QLabel API
        return self._canvas

    def grab(self, *args, **kwargs):  # noqa: ANN001, ANN201
        if self._canvas is not None and not self._canvas.isNull():
            return self._canvas
        return super().grab(*args, **kwargs)

    def refresh(self) -> None:
        if self._pixels is None:
            return
        try:
            work = self._pixels
            if self.show_preprocessed or self.filter_type != FilterType.NONE:
                work = apply_filter(work, self.filter_type)
            windowed = apply_window(work, self.window_center, max(self.window_width, 1.0))
            self._display = to_display_uint8(windowed)
            self._source_pix = QPixmap.fromImage(self._make_qimage(self._display))
            self._compose()
            self.update()
        except Exception as exc:  # noqa: BLE001
            self._error = f"Erreur affichage: {exc}"
            self.update()

    def _make_qimage(self, gray: np.ndarray) -> QImage:
        gray_u8 = np.ascontiguousarray(gray, dtype=np.uint8)
        self._rgb = np.ascontiguousarray(np.stack([gray_u8, gray_u8, gray_u8], axis=-1))
        h, w, _ = self._rgb.shape
        qimg = QImage(self._rgb.data, w, h, 3 * w, QImage.Format_RGB888)
        return qimg.copy()

    def _compose(self) -> None:
        if self._source_pix is None or self._source_pix.isNull():
            return
        tw = max(1, self.width())
        th = max(1, self.height())
        if tw < 20 or th < 20:
            from PySide6.QtCore import QTimer

            QTimer.singleShot(50, self._compose_and_update)
            return

        pix = self._source_pix.copy()
        painter = QPainter(pix)
        pen = QPen(QColor("#39d98a"))
        pen.setWidth(2)
        painter.setPen(pen)
        for x, y, w, h in self._rois:
            painter.drawRect(x, y, w, h)
        pen2 = QPen(QColor("#ff6b6b"))
        pen2.setWidth(2)
        painter.setPen(pen2)
        for p1, p2 in self._measure_lines:
            painter.drawLine(QPointF(*p1), QPointF(*p2))
        if self._img_origin and self._temp_end:
            painter.drawLine(QPointF(*self._img_origin), QPointF(*self._temp_end))
        painter.end()

        scaled = pix.scaled(
            max(1, int(tw * self.zoom)),
            max(1, int(th * self.zoom)),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        canvas = QPixmap(tw, th)
        canvas.fill(QColor("#0b0c0f"))
        p = QPainter(canvas)
        x = int((tw - scaled.width()) / 2 + self.offset.x())
        y = int((th - scaled.height()) / 2 + self.offset.y())
        p.drawPixmap(x, y, scaled)
        p.end()

        self._canvas = canvas
        self._last_scaled_rect = QRectF(x, y, scaled.width(), scaled.height())
        self._last_image_size = (pix.width(), pix.height())
        self._error = None

    def _compose_and_update(self) -> None:
        self._compose()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802, ANN001
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#0b0c0f"))
        if self._error:
            p.setPen(QColor("#ff8a8a"))
            p.drawText(self.rect(), Qt.AlignCenter, self._error)
        elif self._canvas is not None and not self._canvas.isNull():
            p.drawPixmap(0, 0, self._canvas)
        else:
            p.setPen(QColor("#9aa0a6"))
            p.drawText(self.rect(), Qt.AlignCenter, self._placeholder)
        p.end()

    def resizeEvent(self, event) -> None:  # noqa: N802, ANN001
        super().resizeEvent(event)
        if self._source_pix is not None:
            self._compose()
            self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        if self._source_pix is None:
            return
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else (1 / 1.1)
        self.zoom = float(np.clip(self.zoom * factor, 0.2, 8.0))
        self._compose()
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802, ANN001
        if event.button() != Qt.LeftButton:
            return
        self._drag_origin = event.position().toPoint()
        mapped = self._map_to_image(self._drag_origin)
        if self.tool in (ToolMode.MEASURE, ToolMode.ROI) and mapped:
            self._img_origin = mapped
            self._temp_end = mapped
        elif self.tool == ToolMode.PAN:
            self._pan_start = event.position()
            self._offset_start = QPointF(self.offset)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802, ANN001
        if self._drag_origin is None:
            return
        if self.tool == ToolMode.PAN and hasattr(self, "_pan_start"):
            delta = event.position() - self._pan_start
            self.offset = self._offset_start + delta
            self._compose()
            self.update()
            return
        mapped = self._map_to_image(event.position().toPoint())
        if mapped and self._img_origin:
            self._temp_end = mapped
            self._compose()
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802, ANN001
        if event.button() != Qt.LeftButton or self._drag_origin is None:
            return
        mapped = self._map_to_image(event.position().toPoint())
        if self.tool == ToolMode.MEASURE and self._img_origin and mapped:
            self._measure_lines.append((self._img_origin, mapped))
            self.measure_completed.emit(
                self._img_origin[0], self._img_origin[1], mapped[0], mapped[1]
            )
        elif self.tool == ToolMode.ROI and self._img_origin and mapped:
            x0, y0 = self._img_origin
            x1, y1 = mapped
            x, y = int(min(x0, x1)), int(min(y0, y1))
            w, h = int(abs(x1 - x0)), int(abs(y1 - y0))
            if w > 2 and h > 2:
                self._rois.append((x, y, w, h))
                self.roi_completed.emit(x, y, w, h)
        self._drag_origin = None
        self._img_origin = None
        self._temp_end = None
        self._compose()
        self.update()

    def _map_to_image(self, pos: QPoint) -> tuple[float, float] | None:
        rect = self._last_scaled_rect
        if rect.width() <= 0 or rect.height() <= 0:
            return None
        iw, ih = self._last_image_size
        nx = (pos.x() - rect.x()) / rect.width()
        ny = (pos.y() - rect.y()) / rect.height()
        return nx * iw, ny * ih
