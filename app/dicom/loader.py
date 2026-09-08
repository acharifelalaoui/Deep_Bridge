"""DICOM folder loader."""

from __future__ import annotations

import logging
from pathlib import Path

import pydicom
from pydicom.errors import InvalidDicomError

from app.dicom.metadata import dataset_is_demo, extract_metadata
from app.dicom.preprocessing import pixels_from_dataset
from app.dicom.series import DicomSeries, DicomSlice, sort_slices

logger = logging.getLogger("deep_bridge.dicom")


class DicomLoadError(Exception):
    """Raised when a folder cannot yield any readable DICOM series."""


def is_probably_dicom(path: Path) -> bool:
    """Cheap header sniff before full parse."""
    try:
        with path.open("rb") as f:
            preamble = f.read(132)
        if len(preamble) >= 132 and preamble[128:132] == b"DICM":
            return True
        # Some files omit preamble; try extension / allow attempt
        return path.suffix.lower() in {".dcm", ".dicom", ""} or path.suffix == ""
    except OSError:
        return False


def iter_candidate_files(folder: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".txt", ".md", ".json", ".py"}:
            continue
        files.append(path)
    return files


def load_dicom_file(path: Path) -> DicomSlice | None:
    """Load a single DICOM file; return None if not DICOM / unreadable."""
    try:
        ds = pydicom.dcmread(str(path), force=False)
    except InvalidDicomError:
        try:
            ds = pydicom.dcmread(str(path), force=True)
            if not hasattr(ds, "pixel_array"):
                return None
        except Exception as exc:  # noqa: BLE001
            logger.debug("Skip non-DICOM %s (%s)", path.name, type(exc).__name__)
            return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read %s: %s", path.name, type(exc).__name__)
        return None

    if not hasattr(ds, "PixelData") and not hasattr(ds, "pixel_array"):
        return None

    try:
        is_demo = dataset_is_demo(ds)
        meta = extract_metadata(ds, is_demo=is_demo)
        pixels = pixels_from_dataset(ds, meta)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Pixel decode failed for %s: %s", path.name, type(exc).__name__)
        return None

    return DicomSlice(path=path, metadata=meta, pixels=pixels)


def load_dicom_folder(folder: str | Path) -> list[DicomSeries]:
    """
    Recursively load DICOM files from a folder and group by SeriesInstanceUID.

    Non-DICOM files are ignored. Sensitive identifiers are not logged.
    """
    root = Path(folder)
    if not root.exists() or not root.is_dir():
        raise DicomLoadError(f"Folder does not exist: {root}")

    slices: list[DicomSlice] = []
    for path in iter_candidate_files(root):
        item = load_dicom_file(path)
        if item is not None:
            slices.append(item)

    if not slices:
        raise DicomLoadError(f"No readable DICOM images found in {root}")

    by_series: dict[str, list[DicomSlice]] = {}
    for item in slices:
        uid = item.metadata.series_instance_uid or f"unknown-{item.path.parent.name}"
        by_series.setdefault(uid, []).append(item)

    series_list: list[DicomSeries] = []
    for uid, group in by_series.items():
        ordered = sort_slices(group)
        first = ordered[0].metadata
        is_demo = any(s.metadata.is_demo for s in ordered)
        desc = "DEMO DATA – NOT MEDICAL DATA" if is_demo else (first.modality or "Series")
        # Prefer SeriesDescription if present via path marker
        if is_demo:
            desc = "DEMO DATA – NOT MEDICAL DATA"
        series_list.append(
            DicomSeries(
                series_instance_uid=uid,
                study_instance_uid=first.study_instance_uid,
                modality=first.modality,
                description=desc,
                slices=ordered,
                is_demo=is_demo,
            )
        )

    series_list.sort(key=lambda s: (s.modality, s.series_instance_uid))
    logger.info(
        "Loaded %d series (%d slices) from folder (paths redacted).",
        len(series_list),
        sum(s.num_slices for s in series_list),
    )
    return series_list