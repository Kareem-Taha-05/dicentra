"""
tests/test_new_features.py
==========================
Unit tests for Window/Level, histogram, and series-loading additions.
"""
from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


# ── Window / Level ─────────────────────────────────────────────────────────────

from app.logic.image_processor import apply_window_level, compute_histogram


class TestApplyWindowLevel:
    def test_pixels_below_window_become_zero(self):
        arr = np.array([[-1000.0]], dtype=np.float32)
        out = apply_window_level(arr, window_width=400, window_center=40)
        assert out[0, 0] == 0

    def test_pixels_above_window_become_255(self):
        arr = np.array([[5000.0]], dtype=np.float32)
        out = apply_window_level(arr, window_width=400, window_center=40)
        assert out[0, 0] == 255

    def test_center_maps_to_midpoint(self):
        arr = np.array([[40.0]], dtype=np.float32)          # exactly at center
        out = apply_window_level(arr, window_width=400, window_center=40)
        # Center should map to ~127-128
        assert 120 <= int(out[0, 0]) <= 135

    def test_output_dtype_is_uint8(self):
        arr = np.random.uniform(-500, 500, (64, 64)).astype(np.float32)
        out = apply_window_level(arr, 1000, 100)
        assert out.dtype == np.uint8

    def test_bone_preset_values(self):
        # Bone preset: W=1800, C=400
        arr = np.array([[400.0]], dtype=np.float32)
        out = apply_window_level(arr, window_width=1800, window_center=400)
        assert 120 <= int(out[0, 0]) <= 135

    def test_flat_array_with_zero_width_doesnt_crash(self):
        arr = np.zeros((32, 32), dtype=np.float32)
        out = apply_window_level(arr, window_width=1, window_center=0)
        assert out.shape == (32, 32)


class TestComputeHistogram:
    def test_returns_correct_shape(self):
        arr = np.random.rand(128, 128).astype(np.float32) * 1000
        counts, edges = compute_histogram(arr, n_bins=64)
        assert len(counts) == 64
        assert len(edges)  == 65         # n_bins + 1

    def test_counts_sum_to_total_pixels(self):
        arr = np.arange(256, dtype=np.float32).reshape(16, 16)
        counts, _ = compute_histogram(arr, n_bins=32)
        assert counts.sum() == 256

    def test_flat_array_doesnt_crash(self):
        arr = np.full((32, 32), 42.0, dtype=np.float32)
        counts, edges = compute_histogram(arr)
        assert edges[-1] > edges[0]      # range was padded to avoid zero span


# ── Series loading ─────────────────────────────────────────────────────────────

from app.data.dicom_model import SeriesInfo


class TestSeriesInfo:
    def test_dataclass_fields(self):
        info = SeriesInfo(
            series_uid="1.2.3",
            series_description="Brain T1",
            modality="MR",
            study_date="20240101",
            n_slices=48,
            file_paths=["/tmp/a.dcm", "/tmp/b.dcm"],
        )
        assert info.modality == "MR"
        assert info.n_slices == 48
        assert info.thumbnail is None      # default

    def test_thumbnail_accepts_ndarray(self):
        arr  = np.zeros((64, 64), dtype=np.uint8)
        info = SeriesInfo("uid", "desc", "CT", "20240101", 1, [], thumbnail=arr)
        assert info.thumbnail is not None
        assert info.thumbnail.shape == (64, 64)


# ── Colormap / LUT ─────────────────────────────────────────────────────────────

from app.logic.colormap import apply_lut, lut_preview_strip, LUT_NAMES, LUTS


class TestColormaps:
    def test_all_luts_present(self):
        expected = {"Grayscale", "Inverted", "Hot", "Cool", "Viridis", "Plasma", "Bone", "Jet"}
        assert expected.issubset(set(LUT_NAMES))

    def test_lut_shape(self):
        for name, lut in LUTS.items():
            assert lut.shape == (256, 3), f"{name} LUT wrong shape"
            assert lut.dtype == np.uint8,  f"{name} LUT wrong dtype"

    def test_apply_lut_grayscale_identity(self):
        gray = np.arange(256, dtype=np.uint8).reshape(16, 16)
        out  = apply_lut(gray, "Grayscale")
        assert out.shape == (16, 16, 4)
        assert out.dtype == np.uint8
        # R=G=B for grayscale
        np.testing.assert_array_equal(out[:, :, 0], out[:, :, 1])
        np.testing.assert_array_equal(out[:, :, 1], out[:, :, 2])

    def test_apply_lut_all_names_no_crash(self):
        gray = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
        for name in LUT_NAMES:
            out = apply_lut(gray, name)
            assert out.shape == (64, 64, 4)

    def test_alpha_always_255(self):
        gray = np.random.randint(0, 256, (32, 32), dtype=np.uint8)
        out  = apply_lut(gray, "Hot")
        assert np.all(out[:, :, 3] == 255)

    def test_preview_strip_shape(self):
        strip = lut_preview_strip("Viridis", width=200, height=16)
        assert strip.shape == (16, 200, 4)


# ── Ruler / measurement ────────────────────────────────────────────────────────

import math


class TestMeasurementCalc:
    """Test the pure distance math without any Qt display."""

    def _px_dist(self, ax, ay, bx, by, W=512, H=512, ry=1.0, rx=1.0):
        """Replicate RulerCanvas._px_distance logic."""
        dx_px = (bx - ax) * W
        dy_px = (by - ay) * H
        px_d  = math.hypot(dx_px, dy_px)
        mm_d  = math.hypot(dx_px * rx, dy_px * ry) if ry > 0 and rx > 0 else None
        return px_d, mm_d

    def test_horizontal_line(self):
        px, mm = self._px_dist(0, 0.5, 1.0, 0.5)
        assert abs(px - 512) < 0.1
        assert mm is not None and abs(mm - 512) < 0.1

    def test_diagonal_line(self):
        px, mm = self._px_dist(0, 0, 1, 1)
        assert abs(px - math.hypot(512, 512)) < 0.5

    def test_with_pixel_spacing(self):
        # PixelSpacing 0.5mm/px → 512px should be 256mm
        px, mm = self._px_dist(0, 0, 1.0, 0, ry=0.5, rx=0.5)
        assert mm is not None and abs(mm - 256) < 0.5

    def test_zero_length(self):
        px, mm = self._px_dist(0.5, 0.5, 0.5, 0.5)
        assert px == 0.0


# ── Export utilities ───────────────────────────────────────────────────────────

import tempfile, os


class TestExportUtils:
    def test_export_png_grayscale(self, tmp_path):
        from app.logic.export_utils import export_frame_png
        arr  = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
        path = str(tmp_path / "out.png")
        export_frame_png(arr, path)
        assert os.path.exists(path) and os.path.getsize(path) > 0

    def test_export_jpeg_grayscale(self, tmp_path):
        from app.logic.export_utils import export_frame_jpeg
        arr  = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
        path = str(tmp_path / "out.jpg")
        export_frame_jpeg(arr, path)
        assert os.path.exists(path) and os.path.getsize(path) > 0

    def test_export_csv(self, tmp_path):
        from app.logic.export_utils import export_metadata_csv
        from app.data.dicom_model   import TagRow
        tags = [TagRow("(0010,0010)", "Patient Name", "Doe^John")]
        path = str(tmp_path / "meta.csv")
        export_metadata_csv(tags, path)
        assert "Doe^John" in open(path).read()

    def test_export_json(self, tmp_path):
        from app.logic.export_utils import export_metadata_json
        from app.data.dicom_model   import TagRow
        import json
        tags = [TagRow("(0008,0060)", "Modality", "CT")]
        path = str(tmp_path / "meta.json")
        export_metadata_json(tags, path)
        assert json.load(open(path))[0]["value"] == "CT"
