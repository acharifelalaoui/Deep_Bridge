"""Dark professional stylesheet for university demo."""

DARK_STYLESHEET = """
QWidget {
    background-color: #1e1f24;
    color: #e8e8ea;
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}
/* Ne pas peindre par-dessus le viewer DICOM (bug QSS + pixmap sous Windows) */
QWidget#dicomViewer {
    background-color: #0b0c0f;
    border: 1px solid #3a3b42;
}
QLabel {
    background-color: transparent;
}
QMainWindow {
    background-color: #15161a;
}
QPushButton {
    background-color: #2d6cdf;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #3b7af0; }
QPushButton:pressed { background-color: #2457b2; }
QPushButton#dangerBtn { background-color: #a33b3b; }
QPushButton#demoBtn { background-color: #c27c1a; }
QPushButton#demoBtn:hover { background-color: #d48c28; }
QListWidget, QTextEdit, QPlainTextEdit, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #2a2b31;
    border: 1px solid #3a3b42;
    border-radius: 6px;
    padding: 4px;
}
QListWidget::item:selected { background-color: #2d6cdf; }
QSlider::groove:horizontal {
    height: 6px;
    background: #3a3b42;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #2d6cdf;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QLabel#titleLabel {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
}
QLabel#bannerLabel {
    background-color: #5a3a10;
    color: #ffe2a8;
    border: 1px solid #c27c1a;
    border-radius: 6px;
    padding: 8px;
    font-weight: 700;
}
QLabel#disclaimerLabel {
    color: #c9a66b;
    font-size: 11px;
}
QGroupBox {
    border: 1px solid #3a3b42;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QStatusBar { background: #15161a; }
QSplitter::handle { background: #3a3b42; }
"""
