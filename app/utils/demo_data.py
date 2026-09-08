"""Synthetic DEMO DICOM generation helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.utils.paths import DEMO_DIR, ensure_runtime_dirs


def _make_slice(size: int, z: int, n_slices: int) -> np.ndarray:
    """Phantom tres contrasté pour que la DEMO soit visible tout de suite."""
    yy, xx = np.mgrid[0:size, 0:size]
    img = np.full((size, size), 35.0, dtype=np.float32)
    img += 25 * (xx / size)
    # léger soft tissue au centre
    soft = ((xx - size / 2) ** 2 + (yy - size / 2) ** 2) <= (size * 0.28) ** 2
    img[soft] = 70
    shift = int(3 * np.sin(2 * np.pi * z / max(n_slices, 1)))
    vessels = [
        ((size // 2 + 20), (size // 2 - 50 + shift), 18),
        ((size // 2 + 20), (size // 2 + 50 + shift), 16),
    ]
    for cy, cx, r in vessels:
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r**2
        img[mask] = 240
        rim = ((xx - cx) ** 2 + (yy - cy) ** 2 <= (r + 3) ** 2) & ~mask
        img[rim] = 160
    if n_slices // 3 <= z <= 2 * n_slices // 3:
        cy, cx, r = vessels[0]
        narrow = (xx - cx) ** 2 + (yy - cy) ** 2 <= (r - 7) ** 2
        img[narrow] = 45
    noise = np.random.default_rng(z + 1).normal(0, 4, img.shape)
    return np.clip(img + noise, 0, 255).astype(np.uint16)


def generate_demo_series(
    output_dir: Path | None = None,
    n_slices: int = 24,
    size: int = 256,
) -> Path:
    """Write a small DEMO CT-like DICOM series. NOT MEDICAL DATA."""
    import pydicom
    from pydicom.dataset import Dataset, FileDataset
    from pydicom.uid import ExplicitVRLittleEndian, generate_uid

    ensure_runtime_dirs()
    out = Path(output_dir or DEMO_DIR)
    series_dir = out / "demo_carotid_series"
    series_dir.mkdir(parents=True, exist_ok=True)

    for old in series_dir.glob("*.dcm"):
        old.unlink()

    study_uid = generate_uid()
    series_uid = generate_uid()
    frame_of_ref = generate_uid()

    for z in range(n_slices):
        pixel = _make_slice(size, z, n_slices)
        sop_uid = generate_uid()
        filename = series_dir / f"demo_{z:03d}.dcm"

        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = pydicom.uid.CTImageStorage
        file_meta.MediaStorageSOPInstanceUID = sop_uid
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        file_meta.ImplementationClassUID = generate_uid()

        ds = FileDataset(str(filename), {}, file_meta=file_meta, preamble=b"\0" * 128)
        ds.is_little_endian = True
        ds.is_implicit_VR = False
        ds.SOPClassUID = pydicom.uid.CTImageStorage
        ds.SOPInstanceUID = sop_uid
        ds.StudyInstanceUID = study_uid
        ds.SeriesInstanceUID = series_uid
        ds.FrameOfReferenceUID = frame_of_ref
        ds.Modality = "CT"
        ds.SeriesDescription = "DEMO DATA - NOT MEDICAL DATA"
        ds.StudyDescription = "DEMO - Deep Bridge synthetic carotid phantom"
        ds.ImageComments = "DEMO DATA - NOT MEDICAL DATA"
        ds.PatientName = "DEMO^PATIENT"
        ds.PatientID = "DEMO001"
        ds.PatientBirthDate = ""
        ds.PatientSex = "O"
        ds.InstanceNumber = z + 1
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.Rows = size
        ds.Columns = size
        ds.BitsAllocated = 16
        ds.BitsStored = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 0
        ds.RescaleIntercept = 0
        ds.RescaleSlope = 1
        ds.WindowCenter = 120
        ds.WindowWidth = 300
        ds.SliceThickness = 1.0
        ds.PixelSpacing = [0.5, 0.5]
        ds.ImagePositionPatient = [0.0, 0.0, float(z)]
        ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        ds.PixelData = pixel.tobytes()
        ds.save_as(filename, write_like_original=False)

    (out / "README_DEMO.txt").write_text(
        "DEMO DATA – NOT MEDICAL DATA\n"
        "Synthetic DICOM for UI testing only.\n",
        encoding="utf-8",
    )
    return series_dir
