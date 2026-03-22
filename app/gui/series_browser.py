"""
app/gui/series_browser.py
=========================
Left sidebar — three sections stacked vertically:

  ┌─────────────────────────┐
  │  📄 FILE INFO           │  ← current file name, modality, date, size
  ├─────────────────────────┤
  │  📊 QUICK STATS         │  ← slices, dimensions, pixel spacing, HU range
  ├─────────────────────────┤
  │  🕐 RECENT FILES        │  ← last 8 opened files, click to reopen
  ├─────────────────────────┤
  │  📂 SERIES BROWSER      │  ← folder scan + series cards (existing)
  └─────────────────────────┘
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

import numpy as np
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QImage, QPixmap
from PyQt5.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from app.gui.widgets import make_button, make_card, make_separator
from config.settings import SERIES_THUMB_SIZE

# ── Theme helpers ──────────────────────────────────────────────────────────────

_SECTION_STYLE = (
    "color:#C0BCDC; font-family:'Outfit',sans-serif; "
    "font-size:10px; font-weight:600; letter-spacing:1.4px; text-transform:uppercase;"
)
_VALUE_STYLE = (
    "color:#D0CDE8; font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:500;"
)
_MUTED_STYLE = (
    "color:#9490B8; font-family:'JetBrains Mono',monospace; font-size:10px;"
)
_KEY_STYLE = "color:#A8A5C8; font-family:'Outfit',sans-serif; font-size:11px;"

_RECENT_FILE = str(Path.home() / ".dicentra_recent.json")
_MAX_RECENT  = 8

# ── Modality colours ───────────────────────────────────────────────────────────

_MOD_COLORS = {
    "CT": ("#312060","#A78BFA"), "MR": ("#1E2D5A","#60A5FA"),
    "PT": ("#3B2206","#FBB040"), "US": ("#0D3326","#34D399"),
    "CR": ("#9490B8","#C0BCDC"), "DX": ("#9490B8","#C0BCDC"),
}
_DEF_MOD = ("#1E1C30","#B0ADCC")


def _kv_row(key: str, value: str, value_color: str = "#D0CDE8") -> QWidget:
    """One key: value row."""
    w   = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 1, 0, 1)
    lay.setSpacing(6)
    k = QLabel(key)
    k.setStyleSheet(_KEY_STYLE)
    k.setFixedWidth(88)
    v = QLabel(value)
    v.setStyleSheet(
        f"color:{value_color}; font-family:'JetBrains Mono',monospace; "
        f"font-size:11px; font-weight:500;"
    )
    v.setWordWrap(False)
    lay.addWidget(k)
    lay.addWidget(v, stretch=1)
    return w


def _section_hdr(text: str, count: str = "") -> QWidget:
    w   = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 4)
    lay.setSpacing(0)
    lbl = QLabel(text)
    lbl.setStyleSheet(_SECTION_STYLE)
    lay.addWidget(lbl)
    lay.addStretch()
    if count:
        c = QLabel(count)
        c.setStyleSheet(_MUTED_STYLE)
        lay.addWidget(c)
    return w


def _mod_badge(mod: str) -> QLabel:
    bg, fg = _MOD_COLORS.get(mod.upper(), _DEF_MOD)
    lbl = QLabel(mod.upper())
    lbl.setFixedHeight(18)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"background:{bg};color:{fg};border-radius:4px;"
        f"padding:0 8px;font-size:10px;font-weight:600;letter-spacing:0.8px;"
    )
    return lbl


# ── Recent files store ─────────────────────────────────────────────────────────

def _load_recent() -> List[str]:
    try:
        data = json.loads(Path(_RECENT_FILE).read_text())
        return [p for p in data if os.path.exists(p)][:_MAX_RECENT]
    except Exception:
        return []


def _save_recent(paths: List[str]) -> None:
    try:
        Path(_RECENT_FILE).write_text(json.dumps(paths[:_MAX_RECENT]))
    except Exception:
        pass


def add_recent_file(path: str) -> None:
    """Call this whenever a file is loaded successfully."""
    recent = [p for p in _load_recent() if p != path]
    recent.insert(0, path)
    _save_recent(recent[:_MAX_RECENT])


# ── Background scan worker ─────────────────────────────────────────────────────

class _ScanWorker(QObject):
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)

    def __init__(self, folder: str):
        super().__init__()
        self._folder = folder

    def run(self):
        try:
            from app.data.dicom_model import load_series_from_folder
            self.finished.emit(load_series_from_folder(self._folder))
        except Exception as exc:
            self.error.emit(str(exc))


# ── Thumbnail helper ───────────────────────────────────────────────────────────

def _thumb_pixmap(arr, size: int) -> QPixmap:
    if arr is None or not isinstance(arr, np.ndarray):
        px = QPixmap(size, size); px.fill(QColor("#1C1830")); return px
    if arr.ndim != 2: arr = arr.squeeze()
    h, w = arr.shape
    img  = QImage(arr.data, w, h, w, QImage.Format_Grayscale8)
    return QPixmap.fromImage(img).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


# ── Series card ────────────────────────────────────────────────────────────────

class _SeriesCard(QWidget):
    clicked = pyqtSignal(object)

    def __init__(self, info, parent=None):
        super().__init__(parent)
        self._info = info
        self._sel  = False
        self._build()
        self.setCursor(Qt.PointingHandCursor)

    def _build(self):
        self.setFixedHeight(82)
        self.setObjectName("series_card")
        self._apply_style(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 12, 10)
        layout.setSpacing(12)

        thumb = QLabel()
        thumb.setFixedSize(SERIES_THUMB_SIZE, SERIES_THUMB_SIZE)
        thumb.setAlignment(Qt.AlignCenter)
        thumb.setStyleSheet(
            "background:#07050F;border-radius:6px;border:1px solid rgba(124,58,237,0.12);"
        )
        thumb.setPixmap(_thumb_pixmap(self._info.thumbnail, SERIES_THUMB_SIZE))
        layout.addWidget(thumb)

        txt = QVBoxLayout(); txt.setSpacing(4); txt.setContentsMargins(0,0,0,0)
        top = QHBoxLayout(); top.setSpacing(6)
        top.addWidget(_mod_badge(self._info.modality))
        top.addStretch()
        sl  = QLabel(f"{self._info.n_slices} sl")
        sl.setStyleSheet(_MUTED_STYLE)
        top.addWidget(sl)
        txt.addLayout(top)

        desc = QLabel(self._info.series_description or "No description")
        desc.setStyleSheet("color:#D0CDE8;font-size:12px;font-weight:500;")
        desc.setMaximumWidth(145)
        txt.addWidget(desc)

        raw  = self._info.study_date
        date = f"{raw[:4]}-{raw[4:6]}-{raw[6:]}" if len(raw) == 8 else raw or "—"
        dl   = QLabel(date)
        dl.setStyleSheet(_MUTED_STYLE)
        txt.addWidget(dl)
        txt.addStretch()
        layout.addLayout(txt, stretch=1)

    def _apply_style(self, sel: bool):
        if sel:
            self.setStyleSheet("""QWidget#series_card {
                background:rgba(124,58,237,0.12);border:1px solid rgba(124,58,237,0.40);
                border-radius:10px;}""")
        else:
            self.setStyleSheet("""QWidget#series_card {
                background:rgba(255,255,255,0.025);border:1px solid rgba(124,58,237,0.10);
                border-radius:10px;}""")

    def set_selected(self, s: bool): self._sel = s; self._apply_style(s)
    def mousePressEvent(self, _):    self.clicked.emit(self._info)

    def enterEvent(self, _):
        if not self._sel:
            self.setStyleSheet("""QWidget#series_card {
                background:rgba(124,58,237,0.07);border:1px solid rgba(124,58,237,0.22);
                border-radius:10px;}""")

    def leaveEvent(self, _):
        if not self._sel: self._apply_style(False)


# ── Main sidebar widget ────────────────────────────────────────────────────────

class SeriesBrowser(QWidget):
    """
    Full left sidebar.

    Signals
    -------
    series_selected(object)
        str  → folder path to scan
        list → list[str] of .dcm paths to load
    file_reopen_requested(str)
        Emitted when the user clicks a recent file entry.
    """
    series_selected       = pyqtSignal(object)
    file_reopen_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards:  List[_SeriesCard] = []
        self._active: Optional[_SeriesCard] = None
        self._thread: Optional[QThread]     = None
        self._recent: List[str]             = _load_recent()
        self._build()

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build(self):
        self.setFixedWidth(262)
        self.setObjectName("sidebar_panel")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        content = QWidget()
        content.setStyleSheet("background:transparent;")
        vlay = QVBoxLayout(content)
        vlay.setContentsMargins(14, 14, 14, 14)
        vlay.setSpacing(0)

        # ── File Info card ──────────────────────────────────────────────────
        self._file_card = make_card()
        fc_lay = QVBoxLayout(self._file_card)
        fc_lay.setContentsMargins(12, 10, 12, 12)
        fc_lay.setSpacing(6)
        fc_lay.addWidget(_section_hdr("Current File"))

        self._fi_name     = _kv_row("File",      "—")
        self._fi_modality = _kv_row("Modality",  "—")
        self._fi_date     = _kv_row("Date",       "—")
        self._fi_size     = _kv_row("File size",  "—")
        for w in (self._fi_name, self._fi_modality, self._fi_date, self._fi_size):
            fc_lay.addWidget(w)

        vlay.addWidget(self._file_card)
        vlay.addSpacing(10)

        # ── Quick Stats card ────────────────────────────────────────────────
        self._stats_card = make_card()
        sc_lay = QVBoxLayout(self._stats_card)
        sc_lay.setContentsMargins(12, 10, 12, 12)
        sc_lay.setSpacing(6)
        sc_lay.addWidget(_section_hdr("Quick Stats"))

        self._st_dims     = _kv_row("Dimensions", "—")
        self._st_slices   = _kv_row("Frames",     "—")
        self._st_spacing  = _kv_row("Px spacing", "—")
        self._st_hu       = _kv_row("HU range",   "—")
        for w in (self._st_dims, self._st_slices, self._st_spacing, self._st_hu):
            sc_lay.addWidget(w)

        vlay.addWidget(self._stats_card)
        vlay.addSpacing(10)

        # ── Recent Files card ───────────────────────────────────────────────
        self._recent_card = make_card()
        rc_lay = QVBoxLayout(self._recent_card)
        rc_lay.setContentsMargins(12, 10, 12, 12)
        rc_lay.setSpacing(4)
        self._recent_hdr_w = _section_hdr("Recent Files", str(len(self._recent)))
        rc_lay.addWidget(self._recent_hdr_w)

        self._recent_layout = QVBoxLayout()
        self._recent_layout.setSpacing(2)
        self._recent_layout.setContentsMargins(0, 0, 0, 0)
        rc_lay.addLayout(self._recent_layout)
        self._rebuild_recent_list()

        vlay.addWidget(self._recent_card)
        vlay.addSpacing(10)

        # ── Measurements card ──────────────────────────────────────────────
        self._build_measurements_card(vlay)
        vlay.addSpacing(10)

        # ── Series Browser section ──────────────────────────────────────────
        series_card = make_card()
        ser_lay = QVBoxLayout(series_card)
        ser_lay.setContentsMargins(12, 10, 12, 12)
        ser_lay.setSpacing(8)

        ser_hdr = QHBoxLayout()
        ser_title = QLabel("Series")
        ser_title.setStyleSheet(
            "color:#C0BCDC;font-family:'Outfit',sans-serif;"
            "font-size:13px;font-weight:600;letter-spacing:0.5px;"
        )
        ser_hdr.addWidget(ser_title)
        ser_hdr.addStretch()
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(_MUTED_STYLE)
        ser_hdr.addWidget(self._count_lbl)
        ser_lay.addLayout(ser_hdr)

        self._btn_open = QPushButton("📂  Open Folder")
        self._btn_open.setMinimumHeight(38)
        self._btn_open.setCursor(Qt.PointingHandCursor)
        self._btn_open.setStyleSheet("""
            QPushButton {
                background:rgba(124,58,237,0.14);color:#A78BFA;
                border:1px solid rgba(124,58,237,0.32);border-radius:9px;
                font-family:'Outfit',sans-serif;font-size:13px;font-weight:500;
            }
            QPushButton:hover {background:rgba(124,58,237,0.26);color:#C4B5FD;
                               border-color:rgba(124,58,237,0.58);}
            QPushButton:pressed {background:rgba(124,58,237,0.10);}
        """)
        self._btn_open.clicked.connect(self._on_open)
        ser_lay.addWidget(self._btn_open)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedHeight(3)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet("""
            QProgressBar{background:rgba(124,58,237,0.08);border:none;border-radius:1px;}
            QProgressBar::chunk{background:#7C3AED;border-radius:1px;}
        """)
        self._progress.setVisible(False)
        ser_lay.addWidget(self._progress)

        self._scan_status = QLabel("No folder loaded")
        self._scan_status.setStyleSheet(_MUTED_STYLE)
        self._scan_status.setWordWrap(True)
        ser_lay.addWidget(self._scan_status)

        # Series cards container
        self._cards_container = QWidget()
        self._cards_container.setStyleSheet("background:transparent;")
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(6)
        self._cards_layout.addStretch()
        ser_lay.addWidget(self._cards_container)

        vlay.addWidget(series_card)
        vlay.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    # ── Recent files helpers ────────────────────────────────────────────────────

    def _rebuild_recent_list(self):
        while self._recent_layout.count():
            item = self._recent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._recent:
            placeholder = QLabel("No recent files")
            placeholder.setStyleSheet(_MUTED_STYLE)
            self._recent_layout.addWidget(placeholder)
            return

        for path in self._recent:
            name = Path(path).name
            btn  = QPushButton(f"  {name}")
            btn.setFixedHeight(28)
            btn.setToolTip(path)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #C0BCDC;
                    border: none;
                    border-radius: 5px;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 10px;
                    text-align: left;
                    padding: 0 6px;
                }
                QPushButton:hover {
                    background: rgba(124,58,237,0.10);
                    color: #A78BFA;
                }
            """)
            btn.clicked.connect(lambda _, p=path: self.file_reopen_requested.emit(p))
            self._recent_layout.addWidget(btn)


    # ── Measurements card (ruler results forwarded from ImageTab) ──────────────

    def _build_measurements_card(self, parent_layout):
        """Called from _build() to insert the measurements card."""
        self._meas_card = make_card()
        mc_lay = QVBoxLayout(self._meas_card)
        mc_lay.setContentsMargins(12, 10, 12, 12)
        mc_lay.setSpacing(6)

        meas_hdr = QHBoxLayout()
        meas_title = QLabel("Measurements")
        meas_title.setStyleSheet(
            "color:#C0BCDC;font-family:'Outfit',sans-serif;"
            "font-size:10px;font-weight:600;letter-spacing:1.4px;text-transform:uppercase;"
        )
        self._btn_clear_meas = QPushButton("Clear")
        self._btn_clear_meas.setFixedHeight(22)
        self._btn_clear_meas.setEnabled(False)
        # Wire directly — sidebar owns both the button and the clear logic
        self._btn_clear_meas.clicked.connect(self._on_clear_clicked)
        self._btn_clear_meas.setStyleSheet("""
            QPushButton {
                background:rgba(255,107,107,0.08);color:#A05060;
                border:1px solid rgba(255,107,107,0.14);border-radius:5px;
                font-size:10px;font-weight:500;padding:0 8px;
            }
            QPushButton:enabled{color:#F87171;border-color:rgba(255,107,107,0.28);}
            QPushButton:hover:enabled{background:rgba(255,107,107,0.18);
                                      border-color:rgba(255,107,107,0.45);}
        """)
        meas_hdr.addWidget(meas_title); meas_hdr.addStretch()
        meas_hdr.addWidget(self._btn_clear_meas)
        mc_lay.addLayout(meas_hdr)

        self._meas_hint = QLabel("Enable ruler, then drag on the image")
        self._meas_hint.setWordWrap(True)
        self._meas_hint.setStyleSheet(_MUTED_STYLE)
        mc_lay.addWidget(self._meas_hint)

        self._meas_list = QVBoxLayout()
        self._meas_list.setSpacing(3)
        self._meas_list.setContentsMargins(0,0,0,0)
        mc_lay.addLayout(self._meas_list)

        parent_layout.addWidget(self._meas_card)

    def add_measurement(self, label: str):
        """Called when a ruler measurement is completed."""
        # Count current rows
        idx    = self._meas_list.count() + 1
        colors = ["#10B981","#F59E0B","#A78BFA","#FF6B6B","#60A5FA"]
        color  = colors[(idx - 1) % len(colors)]
        row    = QLabel(f"  {idx}.  {label}")
        row.setStyleSheet(
            f"color:{color};font-family:'JetBrains Mono',monospace;"
            f"font-size:11px;font-weight:500;"
        )
        self._meas_list.addWidget(row)
        self._btn_clear_meas.setEnabled(True)
        self._meas_hint.setVisible(False)

    def _on_clear_clicked(self):
        """Internal handler — clears UI and notifies canvas via callback."""
        self.clear_measurements()
        if callable(getattr(self, "_clear_canvas_callback", None)):
            self._clear_canvas_callback()

    def clear_measurements(self):
        """Clear the measurement list UI. Called internally or from main_window."""
        while self._meas_list.count():
            item = self._meas_list.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._btn_clear_meas.setEnabled(False)
        self._meas_hint.setVisible(True)

    def set_clear_canvas_callback(self, fn):
        """Register the function that clears the RulerCanvas (set by main_window)."""
        self._clear_canvas_callback = fn

    def update_recent(self, path: str):
        """Call after each successful file load to refresh the list."""
        add_recent_file(path)
        self._recent = _load_recent()
        self._rebuild_recent_list()
        # update header count
        lbl = self._recent_hdr_w.findChildren(QLabel)
        for l in lbl:
            if l.text().isdigit():
                l.setText(str(len(self._recent)))

    # ── File info / stats update ────────────────────────────────────────────────

    def update_file_info(self, path: str, dataset) -> None:
        """Populate the File Info and Quick Stats cards from a loaded dataset."""
        name  = Path(path).name
        fsize = self._fmt_size(path)

        mod   = str(getattr(dataset, "Modality",   "—"))
        date  = str(getattr(dataset, "StudyDate",  "—"))
        if len(date) == 8:
            date = f"{date[:4]}-{date[4:6]}-{date[6:]}"

        self._set_kv(self._fi_name,     "File",     name,    "#C4C0F0")
        self._set_kv(self._fi_modality, "Modality", mod,     "#A78BFA")
        self._set_kv(self._fi_date,     "Date",     date,    "#D0CDE8")
        self._set_kv(self._fi_size,     "File size", fsize,  "#D0CDE8")

        # Stats
        rows    = str(getattr(dataset, "Rows",    "—"))
        cols    = str(getattr(dataset, "Columns", "—"))
        dims    = f"{cols} × {rows} px"

        n_frames = 1
        try:
            if hasattr(dataset, "NumberOfFrames"):
                n_frames = int(dataset.NumberOfFrames)
            else:
                arr = dataset.pixel_array
                if arr.ndim == 3:
                    n_frames = arr.shape[0]
        except Exception:
            pass

        ps = getattr(dataset, "PixelSpacing", None)
        spacing = f"{float(ps[0]):.3f} mm" if ps else "—"

        hu_range = "—"
        try:
            arr   = dataset.pixel_array
            if arr.ndim == 3: arr = arr[arr.shape[0]//2]
            slope = float(getattr(dataset, "RescaleSlope",     1))
            inter = float(getattr(dataset, "RescaleIntercept", 0))
            hu    = arr.astype(np.float32) * slope + inter
            hu_range = f"{int(hu.min())} → {int(hu.max())} HU"
        except Exception:
            pass

        self._set_kv(self._st_dims,    "Dimensions", dims,           "#C4C0F0")
        self._set_kv(self._st_slices,  "Frames",     str(n_frames),  "#F59E0B")
        self._set_kv(self._st_spacing, "Px spacing", spacing,        "#D0CDE8")
        self._set_kv(self._st_hu,      "HU range",   hu_range,       "#10B981")

    @staticmethod
    def _set_kv(row_widget: QWidget, key: str, value: str, color: str):
        labels = row_widget.findChildren(QLabel)
        if len(labels) >= 2:
            labels[0].setText(key)
            labels[1].setText(value)
            labels[1].setStyleSheet(
                f"color:{color};font-family:'JetBrains Mono',monospace;"
                f"font-size:11px;font-weight:500;"
            )

    @staticmethod
    def _fmt_size(path: str) -> str:
        try:
            b = os.path.getsize(path)
            if b >= 1_048_576: return f"{b/1_048_576:.1f} MB"
            if b >= 1024:      return f"{b/1024:.1f} KB"
            return f"{b} B"
        except Exception:
            return "—"

    # ── Folder scan ────────────────────────────────────────────────────────────

    def _on_open(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select DICOM Folder", "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if folder:
            self._start_scan(folder)

    def _start_scan(self, folder: str):
        self._progress.setVisible(True)
        self._scan_status.setText("Scanning…")
        self._btn_open.setEnabled(False)

        self._thread = QThread()
        self._worker = _ScanWorker(folder)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_scan_done)
        self._worker.error.connect(self._on_scan_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_scan_done(self, series_list: list):
        self._progress.setVisible(False)
        self._btn_open.setEnabled(True)
        self.populate(series_list)

    def _on_scan_error(self, msg: str):
        self._progress.setVisible(False)
        self._btn_open.setEnabled(True)
        self._scan_status.setText(f"Error: {msg}")

    def _on_card_click(self, info):
        if self._active: self._active.set_selected(False)
        for c in self._cards:
            if c._info is info:
                c.set_selected(True); self._active = c; break
        self.series_selected.emit(info.file_paths)

    def populate(self, series_list: list):
        self._cards.clear(); self._active = None
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not series_list:
            self._scan_status.setText("No DICOM series found"); return
        n     = len(series_list)
        total = sum(s.n_slices for s in series_list)
        self._scan_status.setText(f"{n} series · {total} slices")
        self._count_lbl.setText(str(n))
        for info in series_list:
            card = _SeriesCard(info)
            card.clicked.connect(self._on_card_click)
            self._cards.append(card)
            self._cards_layout.insertWidget(self._cards_layout.count()-1, card)
