"""
app/data/dicom_model.py
=======================
Data-access layer. Wraps pydicom — zero Qt imports.
Series loading uses a ThreadPoolExecutor for parallel I/O.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np
import pydicom
from pydicom.dataset import Dataset

logger = logging.getLogger(__name__)

MAX_SCAN_WORKERS   = 8   # parallel header reads
MAX_THUMB_WORKERS  = 4   # parallel thumbnail decodes


@dataclass
class PatientInfo:
    name: str = "N/A"; patient_id: str = "N/A"
    birth_date: str = "N/A"; sex: str = "N/A"

@dataclass
class StudyInfo:
    study_id: str = "N/A"; study_date: str = "N/A"

@dataclass
class ModalityInfo:
    modality: str = "N/A"

@dataclass
class PhysicianInfo:
    name: str = "N/A"; uid: str = "N/A"

@dataclass
class ImageInfo:
    image_type: str = "N/A"; rows: str = "N/A"; columns: str = "N/A"

@dataclass
class PixelDataInfo:
    description: str = "N/A"

@dataclass
class TagRow:
    tag: str; name: str; value: str


class DicomModel:
    def __init__(self) -> None:
        self.dataset:    Optional[Dataset]   = None
        self.frames:     List[np.ndarray]    = []
        self._file_path: str                 = ""

    def load(self, file_path: str) -> None:
        logger.info("Loading: %s", file_path)
        self.dataset    = pydicom.dcmread(file_path)
        self._file_path = file_path
        self._decode_frames()

    def load_series(self, file_paths: list) -> None:
        """Load multiple single-frame DICOM files as a multi-frame volume."""
        import pydicom, numpy as np
        if not file_paths:
            return
        # Sort by InstanceNumber or filename for correct slice order
        def sort_key(p):
            try:
                ds = pydicom.dcmread(p, stop_before_pixels=True)
                return int(getattr(ds, "InstanceNumber", 0))
            except Exception:
                return 0
        sorted_paths = sorted(file_paths, key=sort_key)
        # Use first file as the reference dataset (for tags/metadata)
        self.dataset    = pydicom.dcmread(sorted_paths[0])
        self._file_path = sorted_paths[0]
        self.frames = []
        for p in sorted_paths:
            try:
                ds  = pydicom.dcmread(p)
                arr = ds.pixel_array
                if arr.ndim == 2:
                    self.frames.append(arr)
                elif arr.ndim == 3:
                    for i in range(arr.shape[0]):
                        self.frames.append(arr[i])
            except Exception:
                continue
        logger.info("Series loaded: %d slices from %d files",
                    len(self.frames), len(sorted_paths))

    def _decode_frames(self) -> None:
        if self.dataset is None:
            self.frames = []; return
        try:
            arr = self.dataset.pixel_array
        except AttributeError:
            self.frames = []; return
        if hasattr(self.dataset, "NumberOfFrames") and int(self.dataset.NumberOfFrames) > 1:
            n = int(self.dataset.NumberOfFrames)
            self.frames = [arr[i] for i in range(n)]
        elif arr.ndim == 3:
            self.frames = [arr[i] for i in range(arr.shape[0])]
        else:
            self.frames = [arr]

    @property
    def is_loaded(self)     -> bool: return self.dataset is not None
    @property
    def is_multiframe(self) -> bool: return len(self.frames) > 1
    @property
    def frame_count(self)   -> int:  return len(self.frames)

    def _get(self, attr: str) -> str:
        val = self.dataset.get(attr, "N/A") if self.dataset else "N/A"
        return str(val) if not isinstance(val, str) else val

    def get_patient_info(self)   -> PatientInfo:
        return PatientInfo(self._get("PatientName"), self._get("PatientID"),
                           self._get("PatientBirthDate"), self._get("PatientSex"))
    def get_study_info(self)     -> StudyInfo:
        return StudyInfo(self._get("StudyID"), self._get("StudyDate"))
    def get_modality_info(self)  -> ModalityInfo:
        return ModalityInfo(self._get("Modality"))
    def get_physician_info(self) -> PhysicianInfo:
        return PhysicianInfo(self._get("PhysicianName"), self._get("PhysicianID"))
    def get_image_info(self)     -> ImageInfo:
        img_type = self.dataset.get("ImageType", "N/A") if self.dataset else "N/A"
        if isinstance(img_type, bytes): img_type = img_type.decode("utf-8", errors="ignore")
        else: img_type = str(img_type)
        return ImageInfo(img_type, self._get("Rows"), self._get("Columns"))
    def get_pixel_data_info(self) -> PixelDataInfo:
        if not self.dataset: return PixelDataInfo()
        v = self.dataset.get("PixelData", "N/A")
        return PixelDataInfo(f"Binary data: {len(v):,} bytes" if isinstance(v, bytes) else str(v))

    def get_all_tags(self) -> List[TagRow]:
        if not self.dataset: return []
        return [TagRow(str(e.tag), e.name, str(e.value))
                for e in self.dataset.iterall() if e.name != "Pixel Data"]

    def search_tags(self, query: str) -> List[TagRow]:
        q = query.strip().lower()
        return [TagRow(str(e.tag), e.name, str(e.value))
                for e in self.dataset.iterall() if q in e.name.lower()] if self.dataset else []

    def anonymize(self, prefix: str) -> None:
        if not self.dataset: raise RuntimeError("No DICOM file loaded.")
        self.dataset.PatientName      = f"{prefix}_Patient"
        self.dataset.PatientID        = f"{prefix}_ID"
        self.dataset.StudyID          = f"{prefix}_Study"
        self.dataset.PatientBirthDate = f"{prefix}_BirthDate"
        self.dataset.PatientSex       = "O"

    def save(self, save_path: str) -> None:
        if not self.dataset: raise RuntimeError("No DICOM file loaded.")
        self.dataset.save_as(save_path)


# ── Fast series folder loading ─────────────────────────────────────────────────

@dataclass
class SeriesInfo:
    series_uid:         str
    series_description: str
    modality:           str
    study_date:         str
    n_slices:           int
    file_paths:         list
    thumbnail:          Optional[np.ndarray] = None


def _read_header(fpath: Path):
    """Read only the header (no pixels) — runs in a worker thread."""
    try:
        ds = pydicom.dcmread(str(fpath), stop_before_pixels=True)
        return fpath, ds
    except Exception:
        return None


def _read_thumbnail(fpath: Path) -> Optional[np.ndarray]:
    """Decode pixel data for one file — runs in a worker thread."""
    from app.logic.image_processor import prepare_frame_for_display
    try:
        ds  = pydicom.dcmread(str(fpath))
        arr = ds.pixel_array
        if arr.ndim == 3:
            arr = arr[arr.shape[0] // 2]
        return prepare_frame_for_display(arr)
    except Exception:
        return None


def load_series_from_folder(folder: str) -> List[SeriesInfo]:
    """
    Scan *folder* recursively for .dcm files.

    Performance strategy:
      1. Glob is done once.
      2. Headers are read in parallel (ThreadPoolExecutor, MAX_SCAN_WORKERS).
         pydicom with stop_before_pixels=True is mostly I/O-bound so threads help.
      3. Thumbnails are decoded in parallel (MAX_THUMB_WORKERS), one per series
         (middle slice only).
      4. Results are grouped in-memory after all futures resolve.
    """
    folder_path = Path(folder)
    dcm_files   = list(folder_path.rglob("*.dcm")) + list(folder_path.rglob("*.DCM"))

    if not dcm_files:
        return []

    # ── Phase 1: parallel header reads ────────────────────────────────────
    groups: dict = defaultdict(list)
    with ThreadPoolExecutor(max_workers=MAX_SCAN_WORKERS) as pool:
        futures = {pool.submit(_read_header, f): f for f in dcm_files}
        for fut in as_completed(futures):
            result = fut.result()
            if result is None:
                continue
            fpath, ds = result
            uid = str(getattr(ds, "SeriesInstanceUID", "unknown"))
            groups[uid].append((fpath, ds))

    # ── Phase 2: sort each series and build metadata ───────────────────────
    proto_series: List[SeriesInfo] = []
    thumb_targets: List[tuple]     = []   # (index, mid_path)

    for uid, items in groups.items():
        items.sort(key=lambda x: (int(getattr(x[1], "InstanceNumber", 0)), str(x[0])))
        first_ds = items[0][1]
        info = SeriesInfo(
            series_uid         = uid,
            series_description = str(getattr(first_ds, "SeriesDescription", "Unknown")),
            modality           = str(getattr(first_ds, "Modality", "??")),
            study_date         = str(getattr(first_ds, "StudyDate", "")),
            n_slices           = len(items),
            file_paths         = [str(p) for p, _ in items],
        )
        proto_series.append(info)
        thumb_targets.append((len(proto_series) - 1, items[len(items) // 2][0]))

    # ── Phase 3: parallel thumbnail decodes ───────────────────────────────
    with ThreadPoolExecutor(max_workers=MAX_THUMB_WORKERS) as pool:
        thumb_futures = {pool.submit(_read_thumbnail, path): idx
                         for idx, path in thumb_targets}
        for fut in as_completed(thumb_futures):
            idx   = thumb_futures[fut]
            thumb = fut.result()
            if thumb is not None:
                proto_series[idx].thumbnail = thumb

    proto_series.sort(key=lambda s: (s.study_date, s.series_description), reverse=True)
    return proto_series
