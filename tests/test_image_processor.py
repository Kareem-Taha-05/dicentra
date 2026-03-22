"""
tests/test_image_processor.py
==============================
Unit tests for the image-processing utility functions.
Run with:  pytest tests/
"""

import numpy as np
import pytest

from app.logic.image_processor import (
    apply_rescale,
    normalize_to_uint8,
    prepare_dicom_image,
    prepare_frame_for_display,
    rgb_to_grayscale,
)


class TestNormalizeToUint8:
    def test_normal_range(self):
        arr = np.array([[0.0, 128.0, 255.0]], dtype=np.float32)
        result = normalize_to_uint8(arr)
        assert result.dtype == np.uint8
        assert result[0, 0] == 0
        assert result[0, 2] == 255

    def test_flat_array_returns_zeros(self):
        arr = np.full((4, 4), 42.0, dtype=np.float32)
        result = normalize_to_uint8(arr)
        assert np.all(result == 0)

    def test_output_shape_preserved(self):
        arr = np.random.rand(64, 64).astype(np.float32)
        result = normalize_to_uint8(arr)
        assert result.shape == (64, 64)


class TestApplyRescale:
    def test_slope_intercept(self):
        arr = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
        result = apply_rescale(arr, slope=2.0, intercept=10.0)
        expected = np.array([[12.0, 14.0, 16.0]], dtype=np.float32)
        np.testing.assert_array_almost_equal(result, expected)


class TestRgbToGrayscale:
    def test_output_is_2d(self):
        rgb = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        gray = rgb_to_grayscale(rgb)
        assert gray.ndim == 2
        assert gray.shape == (50, 50)
        assert gray.dtype == np.uint8


class TestPrepareFrameForDisplay:
    def test_2d_input(self):
        frame = np.random.randint(0, 1000, (64, 64), dtype=np.int16)
        result = prepare_frame_for_display(frame)
        assert result is not None
        assert result.dtype == np.uint8
        assert result.shape == (64, 64)

    def test_rgb_input_converts_to_grayscale(self):
        frame = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = prepare_frame_for_display(frame)
        assert result is not None
        assert result.ndim == 2

    def test_invalid_input_returns_none(self):
        result = prepare_frame_for_display("not_an_array")  # type: ignore
        assert result is None


class TestPrepareDicomImage:
    def test_basic(self):
        arr = np.random.randint(0, 4096, (128, 128), dtype=np.int16)
        result = prepare_dicom_image(arr)
        assert result is not None
        assert result.dtype == np.uint8

    def test_with_rescale(self):
        arr = np.ones((32, 32), dtype=np.int16) * 100
        result = prepare_dicom_image(arr, slope=1.0, intercept=0.0)
        assert result is not None
        assert np.all(result == 0)  # flat after rescale → all zeros after normalise
