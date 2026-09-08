"""Point d'entree de l'application Deep Bridge."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication

from app import __version__
from app.ui.main_window import MainWindow
from app.utils.logging_config import setup_logging
from app.utils.paths import ensure_runtime_dirs


def main() -> int:
    print("Deep Bridge: demarrage...", flush=True)
    setup_logging()
    ensure_runtime_dirs()
    app = QApplication(sys.argv)
    app.setApplicationName("Deep Bridge")
    app.setApplicationVersion(__version__)
    window = MainWindow()
    window.statusBar().showMessage("Pret")
    window.show()
    window.raise_()
    window.activateWindow()
    print("Deep Bridge: fenetre ouverte (fermez la fenetre pour quitter).", flush=True)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
