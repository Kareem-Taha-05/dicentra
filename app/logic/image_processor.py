"""
app/logic/image_processor.py
=============================
Image processing utilities for DICOM display.

adjust_window_level() is modelled directly on MedVol's
adjust_brightness_contrast() pattern: it is a pure, stateless function that
takes raw pixel data and returns a uint8 image.  No signals, no caches,
no side-effects.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


# ── Rescale helpers ────────────────────────────────────────────────────────────

def apply_rescale(array: np.ndarray,
                  slope: float, intercept: float) -> np.ndarray:
    return array.astype(np.float32) * slope + intercept


def normalize_to_uint8(array: np.ndarray) -> np.ndarray:
    lo, hi = float(array.min()), float(array.max())
    if hi > lo:
        return ((array - lo) / (hi - lo) * 255.0).astype(np.uint8)
    return np.zeros(array.shape, dtype=np.uint8)


def rgb_to_grayscale(frame: np.ndarray) -> np.ndarray:
    return (0.2989 * frame[:, :, 0]
            + 0.5870 * frame[:, :, 1]
            + 0.1140 * frame[:, :, 2]).astype(np.uint8)


def prepare_frame_for_display(frame: np.ndarray) -> Optional[np.ndarray]:
    if not isinstance(frame, np.ndarray):
        return None
    if frame.ndim == 3:
        frame = rgb_to_grayscale(frame) if frame.shape[2] == 3 else frame.squeeze()
    if frame.ndim != 2:
        return None
    return normalize_to_uint8(frame)


def prepare_dicom_image(pixel_array: np.ndarray,
                        slope: Optional[float] = None,
                        intercept: Optional[float] = None) -> Optional[np.ndarray]:
    arr = pixel_array.astype(np.float32)
    if slope is not None and intercept is not None:
        arr = apply_rescale(arr, slope, intercept)
    return normalize_to_uint8(arr)


# ── Window / Level (the MedVol way) ───────────────────────────────────────────

def apply_window_level(hu_array: np.ndarray,
                       window_width: float,
                       window_center: float) -> np.ndarray:
    """
    Apply DICOM window/level to a float HU array → uint8.

    This is a pure function:
      - Takes raw HU data and W/L parameters
      - Returns a uint8 image
      - No state, no signals, no side-effects

    Exactly how MedVol's adjust_brightness_contrast works:
      read raw data  →  apply transform  →  return display-ready array
    """
    lo = window_center - window_width / 2.0
    hi = window_center + window_width / 2.0
    clipped = np.clip(hu_array, lo, hi)
    if hi > lo:
        scaled = (clipped - lo) / (hi - lo) * 255.0
    else:
        scaled = np.zeros_like(hu_array)
    return scaled.astype(np.uint8)


def compute_histogram(hu_array: np.ndarray, bins: int = 128, n_bins: int = None) -> tuple:
    if n_bins is not None:
        bins = n_bins
    counts, edges = np.histogram(
        hu_array.ravel(), bins=bins,
        range=(float(hu_array.min()), float(hu_array.max()))
    )
    return counts, edges
