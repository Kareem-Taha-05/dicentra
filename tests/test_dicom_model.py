"""
tests/test_dicom_model.py
==========================
Unit tests for the DicomModel data layer (no file I/O – uses mocked datasets).
"""

import numpy as np
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from app.data.dicom_model import DicomModel


def _make_mock_dataset(
    patient_name="Doe^John",
    patient_id="P001",
    num_frames=None,
    pixel_shape=(128, 128),
):
    """Return a minimal mock pydicom Dataset."""
    ds = MagicMock()
    ds.PatientName      = patient_name
    ds.PatientID        = patient_id
    ds.PatientBirthDate = "19800101"
    ds.PatientSex       = "M"
    ds.StudyID          = "S001"
    ds.StudyDate        = "20240101"
    ds.Modality         = "MR"

    # pixel_array
    if num_frames:
        ds.NumberOfFrames = num_frames
        arr = np.zeros((num_frames, *pixel_shape), dtype=np.uint16)
        type(ds).pixel_array = PropertyMock(return_value=arr)
    else:
        arr = np.zeros(pixel_shape, dtype=np.uint16)
        type(ds).pixel_array = PropertyMock(return_value=arr)
        # Make hasattr(ds, 'NumberOfFrames') return False
        del ds.NumberOfFrames

    ds.get = lambda key, default="N/A": getattr(ds, key, default)
    return ds


class TestDicomModelLoad:
    def test_load_sets_dataset(self, tmp_path):
        model = DicomModel()
        fake_ds = _make_mock_dataset()
        with patch("app.data.dicom_model.pydicom.dcmread", return_value=fake_ds):
            model.load(str(tmp_path / "test.dcm"))
        assert model.is_loaded

    def test_load_single_frame(self, tmp_path):
        model = DicomModel()
        fake_ds = _make_mock_dataset(pixel_shape=(64, 64))
        with patch("app.data.dicom_model.pydicom.dcmread", return_value=fake_ds):
            model.load(str(tmp_path / "test.dcm"))
        assert model.frame_count == 1
        assert not model.is_multiframe

    def test_load_multiframe(self, tmp_path):
        model = DicomModel()
        fake_ds = _make_mock_dataset(num_frames=10)
        with patch("app.data.dicom_model.pydicom.dcmread", return_value=fake_ds):
            model.load(str(tmp_path / "test.dcm"))
        assert model.frame_count == 10
        assert model.is_multiframe


class TestDicomModelMetadata:
    def _loaded_model(self, tmp_path):
        model  = DicomModel()
        fake_ds = _make_mock_dataset()
        with patch("app.data.dicom_model.pydicom.dcmread", return_value=fake_ds):
            model.load(str(tmp_path / "test.dcm"))
        return model

    def test_patient_info(self, tmp_path):
        model = self._loaded_model(tmp_path)
        info  = model.get_patient_info()
        assert info.patient_id == "P001"

    def test_study_info(self, tmp_path):
        model = self._loaded_model(tmp_path)
        info  = model.get_study_info()
        assert info.study_id == "S001"

    def test_modality_info(self, tmp_path):
        model = self._loaded_model(tmp_path)
        info  = model.get_modality_info()
        assert info.modality == "MR"


class TestDicomModelAnonymize:
    def test_anonymize_changes_fields(self, tmp_path):
        model   = DicomModel()
        fake_ds = _make_mock_dataset()
        with patch("app.data.dicom_model.pydicom.dcmread", return_value=fake_ds):
            model.load(str(tmp_path / "test.dcm"))
        model.anonymize("ANON")
        assert model.dataset.PatientName == "ANON_Patient"
        assert model.dataset.PatientID   == "ANON_ID"
        assert model.dataset.PatientSex  == "O"

    def test_anonymize_raises_when_not_loaded(self):
        model = DicomModel()
        with pytest.raises(RuntimeError):
            model.anonymize("TEST")
