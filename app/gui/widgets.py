"""app/gui/widgets.py — shared widget helpers, Deep Space Medical theme."""
from __future__ import annotations
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFrame, QLabel, QPushButton, QSizePolicy, QWidget


def make_button(text: str, style: str = "", enabled: bool = True,
                min_width: int = 0, tooltip: str = "") -> QPushButton:
    btn = QPushButton(text)
    if style:       btn.setObjectName(style)
    btn.setEnabled(enabled)
    if min_width:   btn.setMinimumWidth(min_width)
    if tooltip:     btn.setToolTip(tooltip)
    return btn


def make_section_header(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("section_header")
    return lbl


def make_separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Plain)
    return line


def make_card(parent: QWidget = None) -> QWidget:
    """A styled card container (rounded, subtle violet border)."""
    w = QWidget(parent)
    w.setObjectName("control_card")
    return w


def ndarray_to_pixmap(arr: np.ndarray) -> QPixmap:
    """
    Convert a numpy array to a QPixmap.

    Handles all common DICOM pixel array shapes:
      - (H, W)        — grayscale, pass-through
      - (H, W, 3)     — RGB, collapse to grayscale via luminance weights
      - (H, W, 1)     — single-channel 3-D, squeezed to 2-D
      - any other 3-D — first channel used

    Always returns a valid uint8 grayscale pixmap.
    """
    # ── Collapse to 2-D ───────────────────────────────────────────────────
    if arr.ndim == 3:
        if arr.shape[2] == 3:
            # Standard RGB → grayscale luminance
            arr = (0.2989 * arr[:, :, 0]
                   + 0.5870 * arr[:, :, 1]
                   + 0.1140 * arr[:, :, 2]).astype(np.float32)
        elif arr.shape[2] == 1:
            arr = arr[:, :, 0]
        else:
            # Take the middle channel as a best-effort fallback
            arr = arr[:, :, arr.shape[2] // 2]

    if arr.ndim != 2:
        # Absolute fallback: flatten everything, reshape to a square-ish image
        flat = arr.ravel()
        side = int(np.ceil(np.sqrt(len(flat))))
        padded = np.zeros(side * side, dtype=flat.dtype)
        padded[:len(flat)] = flat
        arr = padded.reshape(side, side)

    # ── Ensure uint8 in [0, 255] ──────────────────────────────────────────
    if arr.dtype != np.uint8:
        lo, hi = float(arr.min()), float(arr.max())
        if hi > lo:
            arr = ((arr.astype(np.float32) - lo) / (hi - lo) * 255.0).astype(np.uint8)
        else:
            arr = np.zeros_like(arr, dtype=np.uint8)

    # ── QImage requires a C-contiguous buffer ─────────────────────────────
    arr = np.ascontiguousarray(arr)
    h, w = arr.shape
    img = QImage(arr.data, w, h, w, QImage.Format_Grayscale8)
    # Keep a reference so the buffer isn't GC'd before Qt uses it
    img._numpy_ref = arr
    return QPixmap.fromImage(img)
