"""DICOM metadata helpers with anonymization support."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import pydicom
from pydicom.dataset import Dataset

SENSITIVE_TAGS = (
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientSex",
    "PatientAddress",
    "OtherPatientIDs",
    "OtherPatientNames",
    "ReferringPhysicianName",
    "PerformingPhysicianName",
    "OperatorsName",
    "InstitutionName",
    "InstitutionAddress",
)


@dataclass
class ImageMetadata:
    """Technical metadata useful for display and geometry."""

    study_instance_uid: str = ""
    series_instance_uid: str = ""
    sop_instance_uid: str = ""
    modality: str = ""
    rows: int = 0
    columns: int = 0
    slice_thickness: float | None = None
    pixel_spacing: tuple[float, float] | None = None
    image_position_patient: tuple[float, float, float] | None = None
    image_orientation_patient: tuple[float, ...] | None = None
    window_center: float | None = None
    window_width: float | None = None
    rescale_slope: float = 1.0
    rescale_intercept: float = 0.0
    photometric_interpretation: str = "MONOCHROME2"
    instance_number: int | None = None
    is_demo: bool = False
    anonymized_patient_id: str = "anonymized"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _first_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
            return float(value[0])
        return float(value)
    except (TypeError, ValueError, IndexError):
        return None


def _float_tuple(value: Any, expected: int | None = None) -> tuple[float, ...] | None:
    if value is None:
        return None
    try:
        values = tuple(float(v) for v in value)
        if expected is not None and len(values) != expected:
            return None
        return values
    except (TypeError, ValueError):
        return None


def extract_metadata(ds: Dataset, *, is_demo: bool = False) -> ImageMetadata:
    """Extract technical tags from a DICOM dataset (no PHI in returned fields)."""
    spacing = _float_tuple(getattr(ds, "PixelSpacing", None), expected=2)
    position = _float_tuple(getattr(ds, "ImagePositionPatient", None), expected=3)
    orientation = _float_tuple(getattr(ds, "ImageOrientationPatient", None))

    patient_id = str(getattr(ds, "PatientID", "unknown"))
    anonymized = "DEMO" if is_demo else "anonymized"
    if is_demo:
        anonymized = f"DEMO-{patient_id}" if patient_id else "DEMO"

    return ImageMetadata(
        study_instance_uid=str(getattr(ds, "StudyInstanceUID", "")),
        series_instance_uid=str(getattr(ds, "SeriesInstanceUID", "")),
        sop_instance_uid=str(getattr(ds, "SOPInstanceUID", "")),
        modality=str(getattr(ds, "Modality", "")),
        rows=int(getattr(ds, "Rows", 0) or 0),
        columns=int(getattr(ds, "Columns", 0) or 0),
        slice_thickness=_first_float(getattr(ds, "SliceThickness", None)),
        pixel_spacing=(spacing[0], spacing[1]) if spacing else None,
        image_position_patient=position if position else None,
        image_orientation_patient=orientation,
        window_center=_first_float(getattr(ds, "WindowCenter", None)),
        window_width=_first_float(getattr(ds, "WindowWidth", None)),
        rescale_slope=float(getattr(ds, "RescaleSlope", 1.0) or 1.0),
        rescale_intercept=float(getattr(ds, "RescaleIntercept", 0.0) or 0.0),
        photometric_interpretation=str(
            getattr(ds, "PhotometricInterpretation", "MONOCHROME2")
        ),
        instance_number=(
            int(ds.InstanceNumber)
            if getattr(ds, "InstanceNumber", None) is not None
            else None
        ),
        is_demo=is_demo
        or str(getattr(ds, "SeriesDescription", "")).upper().startswith("DEMO"),
        anonymized_patient_id=anonymized,
    )


def anonymize_dataset(ds: Dataset) -> Dataset:
    """Mask sensitive DICOM tags in-memory (does not write files)."""
    for tag in SENSITIVE_TAGS:
        if hasattr(ds, tag):
            setattr(ds, tag, "ANONYMIZED")
    return ds


def dataset_is_demo(ds: Dataset) -> bool:
    """Detect DEMO marker tags/descriptions."""
    desc = str(getattr(ds, "SeriesDescription", "")).upper()
    study = str(getattr(ds, "StudyDescription", "")).upper()
    comment = str(getattr(ds, "ImageComments", "")).upper()
    return "DEMO" in desc or "DEMO" in study or "NOT MEDICAL" in comment