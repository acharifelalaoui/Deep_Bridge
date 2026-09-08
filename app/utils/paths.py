"""Project path helpers."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DEMO_DIR = DATA_DIR / "demo"
EXPORTS_DIR = PROJECT_ROOT / "exports"
LOGS_DIR = PROJECT_ROOT / "logs"
DOCS_DIR = PROJECT_ROOT / "docs"


def ensure_runtime_dirs() -> None:
    """Create local directories that are safe to write (no patient data)."""
    for path in (EXPORTS_DIR, LOGS_DIR, DEMO_DIR):
        path.mkdir(parents=True, exist_ok=True)