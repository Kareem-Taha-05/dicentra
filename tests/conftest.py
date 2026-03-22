"""
tests/conftest.py
=================
Shared pytest fixtures for the Dicentra test suite.

All fixtures are pure Python — no Qt display required.
"""
from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def sample_hu_array():
    """A small float32 HU array covering a typical CT range."""
    rng = np.random.default_rng(42)
    return rng.uniform(-1000, 3000, (64, 64)).astype(np.float32)


@pytest.fixture
def mock_dicom_dataset():
    """A minimal pydicom Dataset mock with standard CT attributes."""
    ds = MagicMock()
    ds.RescaleSlope     = 1.0
    ds.RescaleIntercept = -1024.0
    ds.Rows             = 64
    ds.Columns          = 64
    ds.BitsAllocated    = 16
    ds.BitsStored       = 12
    ds.PixelRepresentation = 0
    ds.Modality         = "CT"
    ds.PatientName      = "Test^Patient"
    ds.StudyDate        = "20250101"
    return ds


@pytest.fixture
def single_frame_pixel_array():
    """A 64×64 uint16 pixel array (raw CT values before rescale)."""
    rng = np.random.default_rng(0)
    return rng.integers(0, 4096, (64, 64), dtype=np.uint16)
