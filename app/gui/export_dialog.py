"""
app/gui/export_dialog.py
========================
Export Suite dialog — save the current view in several formats.

Options
-------
PNG / JPEG   — current frame with W/L and LUT applied, full resolution
GIF          — all frames of an M2D file as an animated GIF
CSV          — all DICOM metadata tags exported as a spreadsheet
JSON         — same metadata as structured JSON
"""
from __future__ import annotations

import json
import logging
import os
from typing import List, Optional

import numpy as np
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QGroupBox,
    QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QRadioButton, QVBoxLayout, QWidget,
)

logger = logging.getLogger(__name__)


# ── Background GIF worker ──────────────────────────────────────────────────────

class _GifWorker(QObject):
    progress = pyqtSignal(int)      # 0-100
    finished = pyqtSignal(str)      # save path on success
    error    = pyqtSignal(str)

    def __init__(self, frames: List[np.ndarray], path: str, fps: int = 10):
        super().__init__()
        self._frames = frames
        self._path   = path
        self._fps    = fps

    def run(self):
        try:
            import imageio
            total = len(self._frames)
            with imageio.get_writer(self._path, mode="I",
                                    duration=1.0 / self._fps, loop=0) as writer:
                for i, frame in enumerate(self._frames):
                    writer.append_data(frame)
                    self.progress.emit(int((i + 1) / total * 100))
            self.finished.emit(self._path)
        except ImportError:
            self.error.emit("imageio is required for GIF export.\n"
                            "Run: pip install imageio")
        except Exception as exc:
            self.error.emit(str(exc))


# ── Export functions ───────────────────────────────────────────────────────────

def export_frame_png(arr: np.ndarray, path: str) -> None:
    """Save a uint8 array (grayscale or RGBA) as PNG."""
    from PIL import Image
    if arr.ndim == 2:
        Image.fromarray(arr, mode="L").save(path)
    elif arr.shape[2] == 4:
        Image.fromarray(arr, mode="RGBA").save(path)
    else:
        Image.fromarray(arr, mode="RGB").save(path)


def export_frame_jpeg(arr: np.ndarray, path: str, quality: int = 92) -> None:
    from PIL import Image
    if arr.ndim == 2:
        img = Image.fromarray(arr, mode="L")
    elif arr.shape[2] == 4:
        img = Image.fromarray(arr[:, :, :3], mode="RGB")
    else:
        img = Image.fromarray(arr, mode="RGB")
    img.save(path, quality=quality)


def export_metadata_csv(tags, path: str) -> None:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Tag", "Name", "Value"])
        for row in tags:
            writer.writerow([row.tag, row.name, row.value])


def export_metadata_json(tags, path: str) -> None:
    data = [{"tag": r.tag, "name": r.name, "value": r.value} for r in tags]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Dialog ─────────────────────────────────────────────────────────────────────

class ExportDialog(QDialog):
    """
    Modal export dialog.

    Parameters
    ----------
    current_arr   : uint8 ndarray (current rendered frame, grayscale or RGBA)
    all_frames    : list of uint8 ndarrays (for GIF export)
    tags          : list of TagRow (for CSV/JSON)
    is_multiframe : bool
    parent        : QWidget
    """

    def __init__(self, current_arr, all_frames, tags,
                 is_multiframe: bool, parent=None):
        super().__init__(parent)
        self._arr         = current_arr
        self._frames      = all_frames
        self._tags        = tags
        self._is_multi    = is_multiframe
        self._gif_thread  = None

        self.setWindowTitle("Export")
        self.setMinimumWidth(440)
        self.setStyleSheet("""
            QDialog {
                background: #0E0B1A;
                color: #E2E0FF;
                font-family: 'Outfit', sans-serif;
            }
            QGroupBox {
                color: #5A5080;
                border: 1px solid rgba(124,58,237,0.18);
                border-radius: 10px;
                margin-top: 8px;
                padding: 14px 12px 10px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.8px;
                text-transform: uppercase;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px; top: 0px;
                padding: 0 4px;
                background: #0E0B1A;
            }
            QRadioButton {
                color: #8884A8;
                font-size: 13px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 14px; height: 14px;
                border-radius: 7px;
                border: 1px solid rgba(124,58,237,0.35);
                background: #1C1830;
            }
            QRadioButton::indicator:checked {
                background: #7C3AED;
                border-color: #A78BFA;
            }
            QPushButton {
                background: rgba(124,58,237,0.14);
                color: #A78BFA;
                border: 1px solid rgba(124,58,237,0.32);
                border-radius: 8px;
                padding: 8px 20px;
                font-family: 'Outfit', sans-serif;
                font-size: 12px;
                font-weight: 500;
                min-height: 34px;
            }
            QPushButton:hover {
                background: rgba(124,58,237,0.26);
                color: #C4B5FD;
            }
            QPushButton#export_btn {
                background: rgba(16,185,129,0.14);
                color: #10B981;
                border-color: rgba(16,185,129,0.35);
            }
            QPushButton#export_btn:hover {
                background: rgba(16,185,129,0.26);
                color: #34D399;
            }
            QProgressBar {
                background: rgba(124,58,237,0.10);
                border: none; border-radius: 3px; height: 4px;
            }
            QProgressBar::chunk {
                background: #7C3AED; border-radius: 3px;
            }
            QLabel { color: #8884A8; }
            QLabel#result_label { color: #10B981; font-size: 11px; }
            QLabel#result_label[error="true"] { color: #FF6B6B; }
        """)

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # ── Image export ────────────────────────────────────────────────────
        img_box = QGroupBox("Current Frame")
        img_lay = QVBoxLayout(img_box)
        img_lay.setSpacing(8)

        self._rb_png  = QRadioButton("PNG  — lossless, full quality")
        self._rb_jpg  = QRadioButton("JPEG — smaller file, slight compression")
        self._rb_png.setChecked(True)

        img_btn = QPushButton("💾  Save Frame")
        img_btn.setObjectName("export_btn")
        img_btn.clicked.connect(self._export_frame)

        img_lay.addWidget(self._rb_png)
        img_lay.addWidget(self._rb_jpg)
        img_lay.addWidget(img_btn)
        root.addWidget(img_box)

        # ── GIF export ──────────────────────────────────────────────────────
        gif_box = QGroupBox("Animated GIF  (M2D / multi-frame)")
        gif_lay = QVBoxLayout(gif_box)

        gif_note = QLabel(
            "Exports all frames as an animated GIF at 10 fps.\n"
            "Requires imageio  (pip install imageio)"
        )
        gif_note.setWordWrap(True)
        gif_note.setStyleSheet("color:#3D3860; font-size:11px;")

        gif_btn = QPushButton("🎞  Export GIF")
        gif_btn.setObjectName("export_btn")
        gif_btn.setEnabled(self._is_multi)
        if not self._is_multi:
            gif_btn.setToolTip("Load a multi-frame DICOM first")
        gif_btn.clicked.connect(self._export_gif)

        self._gif_progress = QProgressBar()
        self._gif_progress.setVisible(False)

        gif_lay.addWidget(gif_note)
        gif_lay.addWidget(gif_btn)
        gif_lay.addWidget(self._gif_progress)
        root.addWidget(gif_box)

        # ── Metadata export ─────────────────────────────────────────────────
        meta_box = QGroupBox("Metadata")
        meta_lay = QVBoxLayout(meta_box)

        self._rb_csv  = QRadioButton("CSV  — open in Excel / Numbers")
        self._rb_json = QRadioButton("JSON — structured, machine-readable")
        self._rb_csv.setChecked(True)

        meta_btn = QPushButton("📋  Export Metadata")
        meta_btn.setObjectName("export_btn")
        meta_btn.setEnabled(bool(self._tags))
        meta_btn.clicked.connect(self._export_metadata)

        meta_lay.addWidget(self._rb_csv)
        meta_lay.addWidget(self._rb_json)
        meta_lay.addWidget(meta_btn)
        root.addWidget(meta_box)

        # ── Result label ─────────────────────────────────────────────────────
        self._result = QLabel("")
        self._result.setObjectName("result_label")
        self._result.setWordWrap(True)
        root.addWidget(self._result)

        # ── Close ────────────────────────────────────────────────────────────
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        root.addWidget(close_btn, alignment=Qt.AlignRight)

    # ── Export handlers ────────────────────────────────────────────────────────

    def _export_frame(self):
        if self._arr is None:
            self._show_result("No image loaded.", error=True)
            return
        fmt  = "PNG Files (*.png)" if self._rb_png.isChecked() else "JPEG Files (*.jpg *.jpeg)"
        ext  = ".png"              if self._rb_png.isChecked() else ".jpg"
        path, _ = QFileDialog.getSaveFileName(self, "Save Frame", f"frame{ext}", fmt)
        if not path:
            return
        try:
            if self._rb_png.isChecked():
                export_frame_png(self._arr, path)
            else:
                export_frame_jpeg(self._arr, path)
            self._show_result(f"Saved → {os.path.basename(path)}")
        except Exception as exc:
            self._show_result(str(exc), error=True)

    def _export_gif(self):
        if not self._frames:
            self._show_result("No frames available.", error=True)
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Animated GIF", "animation.gif", "GIF Files (*.gif)"
        )
        if not path:
            return

        self._gif_progress.setVisible(True)
        self._gif_progress.setValue(0)

        self._gif_thread  = QThread()
        self._gif_worker  = _GifWorker(self._frames, path)
        self._gif_worker.moveToThread(self._gif_thread)
        self._gif_thread.started.connect(self._gif_worker.run)
        self._gif_worker.progress.connect(self._gif_progress.setValue)
        self._gif_worker.finished.connect(self._on_gif_done)
        self._gif_worker.error.connect(lambda e: self._show_result(e, error=True))
        self._gif_worker.finished.connect(self._gif_thread.quit)
        self._gif_worker.error.connect(self._gif_thread.quit)
        self._gif_thread.start()

    def _on_gif_done(self, path: str):
        self._gif_progress.setVisible(False)
        self._show_result(f"GIF saved → {os.path.basename(path)}")

    def _export_metadata(self):
        if not self._tags:
            self._show_result("No metadata loaded.", error=True)
            return
        if self._rb_csv.isChecked():
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Metadata CSV", "metadata.csv", "CSV Files (*.csv)"
            )
            if path:
                export_metadata_csv(self._tags, path)
                self._show_result(f"CSV saved → {os.path.basename(path)}")
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Metadata JSON", "metadata.json", "JSON Files (*.json)"
            )
            if path:
                export_metadata_json(self._tags, path)
                self._show_result(f"JSON saved → {os.path.basename(path)}")

    def _show_result(self, msg: str, error: bool = False):
        self._result.setProperty("error", "true" if error else "false")
        self._result.setText(("⚠  " if error else "✓  ") + msg)
        self._result.style().unpolish(self._result)
        self._result.style().polish(self._result)
