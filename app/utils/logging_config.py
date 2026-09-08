"""Logging configuration that avoids writing PHI/PII."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.utils.paths import LOGS_DIR, ensure_runtime_dirs

# Tags that must never appear in log messages if avoidable.
SENSITIVE_KEYS = {
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientSex",
    "PatientAddress",
    "OtherPatientIDs",
    "OtherPatientNames",
}


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure console + rotating file logging."""
    ensure_runtime_dirs()
    logger = logging.getLogger("deep_bridge")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    file_handler = RotatingFileHandler(
        LOGS_DIR / "deep_bridge.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("Logging initialise.")
    return logger


def redact_metadata(tag_name: str, value: object) -> str:
    """Return a safe string for logging DICOM tag values."""
    if tag_name in SENSITIVE_KEYS:
        return "<redacted>"
    text = str(value)
    if len(text) > 120:
        return text[:117] + "..."
    return text