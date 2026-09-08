"""DICOM series grouping and ordering."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from app.dicom.metadata import ImageMetadata


@dataclass
class DicomSlice:
    """One image in a series."""

    path: Path
    metadata: ImageMetadata
    pixels: np.ndarray  # float64 after rescale


@dataclass
class DicomSeries:
    """Ordered collection of slices sharing SeriesInstanceUID."""

    series_instance_uid: str
    study_instance_uid: str
    modality: str
    description: str
    slices: list[DicomSlice] = field(default_factory=list)
    is_demo: bool = False

    @property
    def num_slices(self) -> int:
        return len(self.slices)

    @property
    def shape(self) -> tuple[int, int] | None:
        if not self.slices:
            return None
        meta = self.slices[0].metadata
        return meta.rows, meta.columns

    @property
    def pixel_spacing(self) -> tuple[float, float] | None:
        if not self.slices:
            return None
        return self.slices[0].metadata.pixel_spacing

    @property
    def default_window(self) -> tuple[float | None, float | None]:
        if not self.slices:
            return None, None
        meta = self.slices[0].metadata
        return meta.window_center, meta.window_width

    def get_slice(self, index: int) -> DicomSlice:
        if index < 0 or index >= len(self.slices):
            raise IndexError(f"Slice index out of range: {index}")
        return self.slices[index]

    def summary(self) -> str:
        demo = " [DEMO]" if self.is_demo else ""
        return (
            f"{self.modality or 'NA'} | {self.num_slices} slices | "
            f"{self.description or self.series_instance_uid[:12]}{demo}"
        )


def sort_key(slice_: DicomSlice) -> tuple:
    """Sort by InstanceNumber, then ImagePositionPatient Z, then filename."""
    meta = slice_.metadata
    z = 0.0
    if meta.image_position_patient is not None:
        z = meta.image_position_patient[2]
    instance = meta.instance_number if meta.instance_number is not None else 10**9
    return (instance, z, slice_.path.name)


def sort_slices(slices: list[DicomSlice]) -> list[DicomSlice]:
    return sorted(slices, key=sort_key)