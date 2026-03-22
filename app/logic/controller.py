"""
app/logic/controller.py — Dicentra controller.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple

import numpy as np
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from app.data.dicom_model      import DicomModel, TagRow
from app.logic.image_processor import (
    apply_window_level, compute_histogram,
    normalize_to_uint8, prepare_frame_for_display,
    prepare_dicom_image,
)
from config.settings import (
    M2D_FRAME_INTERVAL, WL_DEFAULT_CENTER, WL_DEFAULT_WIDTH, WL_PRESETS,
)

logger = logging.getLogger(__name__)


# ── DICOM tag-group definitions for category filtering ────────────────────────
# Based on DICOM PS3.6 data dictionary — comprehensive tag lists per category.

_PATIENT_TAGS = {
    "PatientName", "PatientID", "PatientBirthDate", "PatientSex",
    "PatientAge", "PatientWeight", "PatientSize", "PatientAddress",
    "PatientTelephoneNumbers", "PatientMotherBirthName", "PatientReligiousPreference",
    "PatientComments", "PatientSpeciesDescription", "PatientBreedDescription",
    "ResponsiblePerson", "ResponsibleOrganization", "OtherPatientNames",
    "OtherPatientIDs", "PatientAlternativeCalendar", "PatientDeathDateInAlternativeCalendar",
    "PatientBirthDateInAlternativeCalendar", "PatientBirthTime", "PatientInsurancePlanCodeSequence",
    "PatientPrimaryLanguageCodeSequence", "PatientEthnicGroup",
    "PatientOccupation", "SmokingStatus", "AdditionalPatientHistory",
    "PregnancyStatus", "LastMenstrualDate", "PatientSexNeutered",
    "SpecialNeeds", "PatientState", "PertinentDocumentsSequence",
    "ClinicalTrialSubjectID", "ClinicalTrialSubjectReadingID",
    "ClinicalTrialProtocolID", "ClinicalTrialProtocolName",
    "ClinicalTrialSiteID", "ClinicalTrialSiteName",
}

_STUDY_TAGS = {
    "StudyInstanceUID", "StudyID", "StudyDate", "StudyTime",
    "StudyDescription", "AccessionNumber", "ReferringPhysicianName",
    "StudyStatusID", "StudyPriorityID", "ReasonForStudy",
    "RequestedProcedureDescription", "RequestedProcedureCodeSequence",
    "AdmissionID", "AdmittingDiagnosesDescription", "AdmittingDiagnosesCodeSequence",
    "PatientAge", "PatientWeight", "PatientSize",
    "NumberOfStudyRelatedSeries", "NumberOfStudyRelatedInstances",
    "RequestingService", "RequestingPhysician", "IssueDateOfImagingServiceRequest",
    "IssueTimeOfImagingServiceRequest", "PlacerOrderNumberImagingServiceRequest",
    "FillerOrderNumberImagingServiceRequest", "OrderEnteredBy",
    "OrderEntererLocation", "OrderCallbackPhoneNumber",
    "ClinicalTrialTimePointID", "ClinicalTrialTimePointDescription",
}

_SERIES_MODALITY_TAGS = {
    "Modality", "SeriesInstanceUID", "SeriesNumber", "SeriesDate", "SeriesTime",
    "SeriesDescription", "BodyPartExamined", "PatientPosition",
    "SmallestPixelValueInSeries", "LargestPixelValueInSeries",
    "ProtocolName", "PerformedProcedureStepStartDate", "PerformedProcedureStepStartTime",
    "PerformedProcedureStepDescription", "PerformedProcedureStepID",
    "RequestAttributesSequence", "CommentsOnThePerformedProcedureStep",
    "AcquisitionDate", "AcquisitionTime", "AcquisitionNumber",
    "AcquisitionDuration", "ImagesInAcquisition",
    "ScanningSequence", "SequenceVariant", "ScanOptions", "MRAcquisitionType",
    "SequenceName", "AngioFlag", "SliceThickness", "RepetitionTime",
    "EchoTime", "InversionTime", "NumberOfAverages", "ImagingFrequency",
    "ImagedNucleus", "EchoNumbers", "MagneticFieldStrength",
    "NumberOfPhaseEncodingSteps", "EchoTrainLength", "PercentSampling",
    "PercentPhaseFieldOfView", "PixelBandwidth", "DeviceSerialNumber",
    "SoftwareVersions", "ReceiveCoilName", "TransmitCoilName",
    "FlipAngle", "VariableFlipAngleFlag", "SAR", "dBdt",
    "ContrastBolusAgent", "ContrastBolusRoute", "ContrastBolusVolume",
    "ContrastBolusStartTime", "ContrastBolusStopTime",
    "ContrastBolusTotalDose", "ContrastFlowRate",
    "ExposureTime", "XRayTubeCurrent", "Exposure", "ExposureInuAs",
    "FilterType", "GeneratorPower", "FocalSpots",
    "ConvolutionKernel", "KVP", "DataCollectionDiameter",
    "ReconstructionDiameter", "GantryDetectorTilt", "TableHeight",
    "RotationDirection", "ExposureModulationType",
    "CTDIvol", "FocalSpots", "RevolutionTime",
}

_EQUIPMENT_PHYSICIAN_TAGS = {
    "Manufacturer", "ManufacturerModelName", "DeviceSerialNumber",
    "SoftwareVersions", "InstitutionName", "InstitutionAddress",
    "StationName", "InstitutionalDepartmentName", "OperatorsName",
    "PerformingPhysicianName", "PerformingPhysicianIdentificationSequence",
    "ReferringPhysicianName", "ReferringPhysicianIdentificationSequence",
    "NameOfPhysiciansReadingStudy", "PhysiciansReadingStudyIdentificationSequence",
    "RequestingPhysician", "ScheduledPerformingPhysicianName",
    "LastCalibrationDate", "LastCalibrationTime",
}

_IMAGE_TAGS = {
    "ImageType", "SOPClassUID", "SOPInstanceUID",
    "InstanceNumber", "ImageNumber", "FrameTime", "FrameTimeVector",
    "StartTrim", "StopTrim", "RecommendedDisplayFrameRate",
    "FrameDelay", "FrameLabelVector", "FrameVectorType",
    "SliceLocation", "SliceThickness",
    "ImageOrientationPatient", "ImagePositionPatient",
    "FrameOfReferenceUID", "PositionReferenceIndicator",
    "WindowCenter", "WindowWidth", "WindowCenterWidthExplanation",
    "RescaleIntercept", "RescaleSlope", "RescaleType",
    "VOILUTSequence", "VOILUTFunction",
    "PhotometricInterpretation", "SamplesPerPixel",
    "PlanarConfiguration", "NumberOfFrames",
    "PixelAspectRatio", "PixelSpacing", "ImagerPixelSpacing",
    "FieldOfViewDimensions", "FieldOfViewOrigin", "FieldOfViewRotation",
    "SmallestImagePixelValue", "LargestImagePixelValue",
    "SmallestPixelValueInSeries", "LargestPixelValueInSeries",
    "PixelPaddingValue", "PixelPaddingRangeLimit",
    "LossyImageCompression", "LossyImageCompressionRatio",
    "LossyImageCompressionMethod",
    "PresentationLUTShape", "LossyImageCompressionRetired",
}

_PIXEL_TAGS = {
    "PixelData", "Rows", "Columns", "BitsAllocated", "BitsStored",
    "HighBit", "PixelRepresentation", "SamplesPerPixel",
    "PlanarConfiguration", "NumberOfFrames",
    "PixelSpacing", "ImagerPixelSpacing", "NominalScannedPixelSpacing",
    "PixelAspectRatio", "PixelDataProviderURL",
    "ExtendedOffsetTable", "ExtendedOffsetTableLengths",
    "FloatPixelData", "DoubleFloatPixelData",
    "PixelDataQualitySequence", "EncapsulatedPixelDataValueTotalLength",
}


class DicomController(QObject):
    file_loaded         = pyqtSignal(str)
    image_ready         = pyqtSignal(object)
    frame_ready         = pyqtSignal(object)
    playback_stopped    = pyqtSignal()
    status_message      = pyqtSignal(str)
    metadata_rows_ready = pyqtSignal(object)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._model      = DicomModel()
        self._m2d_timer  = QTimer(self)
        self._m2d_index  = 0
        self._m2d_timer.timeout.connect(self._on_frame_tick)

    @property
    def is_loaded(self)     -> bool: return self._model.is_loaded
    @property
    def is_multiframe(self) -> bool: return self._model.is_multiframe
    @property
    def frame_count(self)   -> int:  return self._model.frame_count

    def load_file(self, file_path: str) -> None:
        try:
            self._model.load(file_path)
        except Exception as exc:
            self.status_message.emit(f"Load failed: {exc}")
            return
        self.file_loaded.emit(file_path)
        self.status_message.emit(f"Loaded: {file_path.replace(chr(92),'/').split('/')[-1]}")

    def display_image(self) -> None:
        if not self._model.is_loaded:
            self.status_message.emit("No DICOM file loaded.")
            return
        if not self._model.frames:
            self.status_message.emit("No pixel data found.")
            return
        if self._model.is_multiframe:
            self._start_playback()
        else:
            self._show_static_image()

    def _show_static_image(self) -> None:
        ds        = self._model.dataset
        slope     = float(ds.RescaleSlope)     if hasattr(ds, "RescaleSlope")     else None
        intercept = float(ds.RescaleIntercept) if hasattr(ds, "RescaleIntercept") else None
        arr = prepare_dicom_image(self._model.frames[0], slope, intercept)
        if arr is None:
            self.status_message.emit("Could not process pixel data.")
            return
        self.image_ready.emit(arr)
        self.status_message.emit("Image displayed.")

    def _start_playback(self) -> None:
        self._m2d_index = 0
        self._m2d_timer.start(M2D_FRAME_INTERVAL)
        self.status_message.emit(f"Playing  ·  {self._model.frame_count} frames")

    def _on_frame_tick(self) -> None:
        if self._m2d_index >= self._model.frame_count:
            self.stop_playback(); return
        frame = self._model.frames[self._m2d_index]
        arr   = prepare_frame_for_display(frame)
        if arr is not None:
            self.frame_ready.emit(arr)
        self._m2d_index += 1

    def stop_playback(self) -> None:
        if self._m2d_timer.isActive():
            self._m2d_timer.stop()
        self.playback_stopped.emit()
        self.status_message.emit("Playback stopped.")

    # ── Metadata ───────────────────────────────────────────────────────────────

    def _tags_for_names(self, name_set: set) -> List[TagRow]:
        """Return all TagRows whose keyword name is in name_set."""
        if not self._model.is_loaded:
            return []
        results = []
        for e in self._model.dataset.iterall():
            if e.name in name_set or e.keyword in name_set:
                results.append(TagRow(str(e.tag), e.name or e.keyword, str(e.value)))
        return results

    def get_all_tags(self)      -> None: self.metadata_rows_ready.emit(self._model.get_all_tags())
    def search_tags(self, q)    -> None: self.metadata_rows_ready.emit(self._model.search_tags(q))
    def get_patient_info(self)  -> None: self.metadata_rows_ready.emit(self._tags_for_names(_PATIENT_TAGS))
    def get_study_info(self)    -> None: self.metadata_rows_ready.emit(self._tags_for_names(_STUDY_TAGS))
    def get_modality_info(self) -> None: self.metadata_rows_ready.emit(self._tags_for_names(_SERIES_MODALITY_TAGS))
    def get_physician_info(self)-> None: self.metadata_rows_ready.emit(self._tags_for_names(_EQUIPMENT_PHYSICIAN_TAGS))
    def get_image_info(self)    -> None: self.metadata_rows_ready.emit(self._tags_for_names(_IMAGE_TAGS))
    def get_pixel_data_info(self)->None: self.metadata_rows_ready.emit(self._tags_for_names(_PIXEL_TAGS))

    def anonymize_and_save(self, prefix: str, save_path: str) -> None:
        try:
            self._model.anonymize(prefix)
            self._model.save(save_path)
            self.status_message.emit(f"Saved anonymised: {save_path}")
        except Exception as exc:
            self.status_message.emit(f"Anonymise failed: {exc}")

    def get_tile_frames(self) -> Tuple[List[np.ndarray], str]:
        if not self._model.is_loaded or not self._model.frames:
            return [], ""
        frames = [f for f in (prepare_frame_for_display(fr) for fr in self._model.frames) if f is not None]
        return frames, f"{len(frames)} frames"


# ══════════════════════════════════════════════════════════════════════════════

class DicomControllerExtended(DicomController):
    wl_changed      = pyqtSignal(float, float)
    wl_render_ready = pyqtSignal(object)
    histogram_ready = pyqtSignal(object, object)
    series_loaded   = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._wl_width:      float            = WL_DEFAULT_WIDTH
        self._wl_center:     float            = WL_DEFAULT_CENTER
        self.raw_hu_frames:  List[np.ndarray] = []
        self._display_index: int              = 0

    @property
    def wl_width(self)          -> float: return self._wl_width
    @property
    def wl_center(self)         -> float: return self._wl_center
    @property
    def current_frame_index(self) -> int:  return self._display_index
    @property
    def is_playing(self)        -> bool:  return self._m2d_timer.isActive()

    def _redisplay(self) -> None:
        if not self.raw_hu_frames: return
        idx = max(0, min(self._display_index, len(self.raw_hu_frames) - 1))
        arr = apply_window_level(self.raw_hu_frames[idx], self._wl_width, self._wl_center)
        self.wl_render_ready.emit(arr)

    def _redisplay_with_histogram(self) -> None:
        if not self.raw_hu_frames: return
        idx = max(0, min(self._display_index, len(self.raw_hu_frames) - 1))
        hu  = self.raw_hu_frames[idx]
        arr = apply_window_level(hu, self._wl_width, self._wl_center)
        self.wl_render_ready.emit(arr)
        counts, edges = compute_histogram(hu)
        self.histogram_ready.emit(counts, edges)

    def set_window_level(self, width: float, center: float) -> None:
        self._wl_width  = max(1.0, float(width))
        self._wl_center = float(center)
        self._redisplay()
        self.wl_changed.emit(self._wl_width, self._wl_center)

    def apply_preset(self, name: str) -> None:
        if name in WL_PRESETS:
            w, c = WL_PRESETS[name]
            self.set_window_level(w, c)

    def load_file(self, file_path: str) -> None:
        self._wl_width      = WL_DEFAULT_WIDTH
        self._wl_center     = WL_DEFAULT_CENTER
        self._display_index = 0
        self.raw_hu_frames  = []
        super().load_file(file_path)
        self._build_hu_frames()

    def _build_hu_frames(self) -> None:
        if not self._model.is_loaded or not self._model.frames: return
        ds        = self._model.dataset
        slope     = float(ds.RescaleSlope)     if hasattr(ds, "RescaleSlope")     else 1.0
        intercept = float(ds.RescaleIntercept) if hasattr(ds, "RescaleIntercept") else 0.0
        self.raw_hu_frames = []
        for frame in self._model.frames:
            raw = frame.astype(np.float32)
            if raw.ndim == 3:
                raw = (0.2989*raw[:,:,0]+0.5870*raw[:,:,1]+0.1140*raw[:,:,2]) if raw.shape[2]==3 else raw.squeeze()
            self.raw_hu_frames.append(raw * slope + intercept)
        if self.raw_hu_frames:
            mid = self.raw_hu_frames[len(self.raw_hu_frames) // 2]
            lo  = float(np.percentile(mid, 1))
            hi  = float(np.percentile(mid, 99))
            self._wl_width  = max(1.0, hi - lo)
            self._wl_center = (hi + lo) / 2.0

    def _show_static_image(self) -> None:
        self._display_index = 0
        self._redisplay_with_histogram()
        self.status_message.emit(f"Displayed  ·  W:{int(self._wl_width)}  C:{int(self._wl_center)}")

    def _on_frame_tick(self) -> None:
        if self._m2d_index >= len(self.raw_hu_frames):
            self.stop_playback(); return
        self._display_index = self._m2d_index
        self._m2d_index    += 1
        hu  = self.raw_hu_frames[self._display_index]
        arr = apply_window_level(hu, self._wl_width, self._wl_center)
        self.frame_ready.emit(arr)

    def seek_frame(self, index: int) -> None:
        if not self.raw_hu_frames: return
        index = max(0, min(index, len(self.raw_hu_frames) - 1))
        if self._m2d_timer.isActive():
            self._m2d_timer.stop(); self.playback_stopped.emit()
        self._m2d_index = self._display_index = index
        hu  = self.raw_hu_frames[index]
        arr = apply_window_level(hu, self._wl_width, self._wl_center)
        self.frame_ready.emit(arr)
        counts, edges = compute_histogram(hu)
        self.histogram_ready.emit(counts, edges)
        self.status_message.emit(f"Frame {index+1} / {len(self.raw_hu_frames)}")

    def step_frame(self, delta: int) -> None:
        self.seek_frame(self._display_index + delta)

    def pause_playback(self) -> None:
        if self._m2d_timer.isActive():
            self._m2d_timer.stop(); self.playback_stopped.emit()
            self.status_message.emit(f"Paused  ·  frame {self._display_index+1} / {len(self.raw_hu_frames)}")

    def resume_playback(self) -> None:
        if self.raw_hu_frames and not self._m2d_timer.isActive():
            self._m2d_timer.start(M2D_FRAME_INTERVAL)
            self.status_message.emit("Resumed playback")

    def load_series_folder(self, folder_path: str) -> None:
        try:
            from app.data.dicom_model import load_series_from_folder
            series = load_series_from_folder(folder_path)
        except Exception as exc:
            self.status_message.emit(f"Folder scan failed: {exc}"); return
        if not series:
            self.status_message.emit("No readable DICOM files found."); return
        self.series_loaded.emit(series)
        self.status_message.emit(f"Found {len(series)} series")

    def load_series_by_paths(self, file_paths: List[str]) -> None:
        """Load a list of single-frame DICOM files as a multi-frame volume."""
        if not file_paths: return
        self._wl_width      = WL_DEFAULT_WIDTH
        self._wl_center     = WL_DEFAULT_CENTER
        self._display_index = 0
        self.raw_hu_frames  = []
        # Load all slices into the model as a multi-frame volume
        try:
            self._model.load_series(file_paths)
        except Exception as exc:
            self.status_message.emit(f"Series load failed: {exc}")
            return
        self.file_loaded.emit(file_paths[0])
        self.status_message.emit(
            f"Series loaded  ·  {len(file_paths)} files  ·  "
            f"{self._model.frame_count} slices"
        )
        self._build_hu_frames()
