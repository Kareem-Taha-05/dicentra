"""
app/gui/image_tab.py  — Image Viewer tab.

Right panel: W/L card + Histogram card only (both scrollable, no cramping).
Measurements moved to the left sidebar (series_browser.py).
Nav bar: taller (68px), proper Unicode symbols, full bottom padding.
"""
from __future__ import annotations

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QSlider, QVBoxLayout, QWidget, QFrame,
)

from app.gui.colormap_bar    import ColormapBar
from app.gui.export_dialog   import ExportDialog
from app.gui.histogram_panel import HistogramPanel
from app.gui.ruler_canvas    import RulerCanvas
from app.gui.widgets         import make_button, make_card, ndarray_to_pixmap
from app.gui.wl_panel        import WLPanel
from config.settings import WL_PRESETS
from app.logic.colormap      import apply_lut


# ── Click-to-position slider ──────────────────────────────────────────────────

class ClickJumpSlider(QSlider):
    """
    QSlider that:
    - Jumps to the exact clicked pixel position (not ±pageStep)
    - Still allows click-and-drag to slide smoothly
    """

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton and self.maximum() > self.minimum():
            # 1. Move handle to clicked position immediately
            self._jump_to(ev.pos().x())
            # 2. Call super() so Qt starts its normal drag tracking — this
            #    is what was missing before; without it dragging stopped working
            super().mousePressEvent(ev)
        else:
            super().mousePressEvent(ev)

    def _jump_to(self, pixel_x: int) -> None:
        # Account for the handle width so the mapping is accurate at the edges
        handle_w = self.style().pixelMetric(
            self.style().PM_SliderLength, None, self
        )
        usable = max(1, self.width() - handle_w)
        offset = handle_w // 2
        rel    = max(0, min(pixel_x - offset, usable))
        ratio  = rel / usable
        value  = round(self.minimum() + ratio * (self.maximum() - self.minimum()))
        self.setValue(value)


# ── Nav button helpers ─────────────────────────────────────────────────────────

_NAV_SS = """
    QPushButton {
        background: rgba(255,255,255,0.04);
        color: #D0CDE8;
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 7px;
    }
    QPushButton:hover {
        background: rgba(124,58,237,0.18);
        color: #C4B5FD;
        border-color: rgba(124,58,237,0.42);
    }
    QPushButton:pressed { background: rgba(124,58,237,0.08); }
    QPushButton:disabled {
        color: #6B6890;
        border-color: rgba(255,255,255,0.04);
        background: transparent;
    }
"""

def _nav_btn(text: str, tooltip: str = "") -> QPushButton:
    btn = QPushButton(text)
    btn.setFixedSize(58, 38)
    btn.setStyleSheet(_NAV_SS)
    if tooltip:
        btn.setToolTip(tooltip)
    return btn


def _play_btn() -> QPushButton:
    btn = QPushButton(">")
    btn.setFixedSize(58, 38)
    btn.setToolTip("Play / Pause  (Space)")
    btn.setStyleSheet("""
        QPushButton {
            background: rgba(124,58,237,0.20);
            color: #A78BFA;
            border: 1px solid rgba(124,58,237,0.42);
            border-radius: 8px;
        }
        QPushButton:hover {
            background: rgba(124,58,237,0.34);
            color: #C4B5FD;
            border-color: rgba(124,58,237,0.70);
        }
        QPushButton:pressed { background: rgba(124,58,237,0.12); }
        QPushButton:disabled {
            color: #6B6890;
            border-color: rgba(124,58,237,0.08);
            background: transparent;
        }
    """)
    return btn


def _scrubber() -> ClickJumpSlider:
    s = ClickJumpSlider(Qt.Horizontal)
    s.setRange(0, 0); s.setValue(0)
    s.setStyleSheet("""
        QSlider::groove:horizontal {
            height: 5px; background: rgba(124,58,237,0.14); border-radius: 2px;
        }
        QSlider::handle:horizontal {
            width: 18px; height: 18px; border-radius: 9px;
            background: #A78BFA; margin: -7px 0;
            border: 2px solid rgba(196,181,253,0.60);
        }
        QSlider::handle:horizontal:hover {
            background: #C4B5FD; border-color: rgba(196,181,253,0.90);
        }
        QSlider::sub-page:horizontal {
            background: rgba(124,58,237,0.45); border-radius: 2px;
        }
    """)
    return s


# ── Tab widget ─────────────────────────────────────────────────────────────────

class ImageTab(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._ctrl          = controller
        self._frame_idx     = 0
        self._active_lut    = "Grayscale"
        self._last_gray     = None
        self._all_rendered  = []
        self._scrubber_lock = False
        # Measurement signal targets — filled by main_window after construction
        self.on_measurement_added   = None   # callable(label)
        self.on_measurements_cleared = None  # callable()
        self._setup_ui()
        self._connect_signals()

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)   # extra bottom margin
        root.setSpacing(0)

        # ── Toolbar ────────────────────────────────────────────────────────
        tb = QHBoxLayout(); tb.setSpacing(8); tb.setContentsMargins(0,0,0,12)
        self._btn_load   = make_button("📂  Load",   "primary", min_width=100,
                                       tooltip="Open a .dcm file")
        self._btn_ruler  = make_button("📏  Ruler",  enabled=False, min_width=88,
                                       tooltip="Toggle ruler: drag to measure distance")
        self._btn_export = make_button("💾  Export", enabled=False, min_width=88,
                                       tooltip="Export frame, GIF, or metadata")
        self._btn_ruler.setCheckable(True)
        tb.addWidget(self._btn_load); tb.addSpacing(4)
        tb.addWidget(self._btn_ruler); tb.addWidget(self._btn_export)
        tb.addStretch()
        root.addLayout(tb)

        # ── Colormap bar ───────────────────────────────────────────────────
        cmap_card = make_card(); cmap_card.setFixedHeight(62)
        cmap_lay  = QVBoxLayout(cmap_card); cmap_lay.setContentsMargins(12,6,12,6)
        self._cmap_bar = ColormapBar()
        cmap_lay.addWidget(self._cmap_bar)
        root.addWidget(cmap_card)
        root.addSpacing(12)

        # ── Body ───────────────────────────────────────────────────────────
        body = QHBoxLayout(); body.setSpacing(16); body.setContentsMargins(0,0,0,0)

        self._canvas = RulerCanvas()
        body.addWidget(self._canvas, stretch=1)

        vl = QFrame(); vl.setFrameShape(QFrame.VLine)
        vl.setStyleSheet("background:rgba(124,58,237,0.10);border:none;max-width:1px;min-width:1px;")
        body.addWidget(vl)

        # ── Right panel: scrollable, W/L + Histogram only ──────────────────
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFixedWidth(298)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        right_scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        right_inner = QWidget()
        right_inner.setStyleSheet("background:transparent;")
        right = QVBoxLayout(right_inner)
        right.setSpacing(12); right.setContentsMargins(0, 0, 6, 0)

        # W/L card — full height, not clipped
        # ── Sliders card ────────────────────────────────────────────────────
        wl_card = make_card()
        wl_vl   = QVBoxLayout(wl_card); wl_vl.setContentsMargins(0,0,0,0)
        self._wl_panel = WLPanel()
        wl_vl.addWidget(self._wl_panel)
        right.addWidget(wl_card)

        # ── Histogram card ───────────────────────────────────────────────────
        hist_card = make_card()
        hist_vl   = QVBoxLayout(hist_card); hist_vl.setContentsMargins(0,0,0,0)
        self._hist_panel = HistogramPanel()
        hist_vl.addWidget(self._hist_panel)
        right.addWidget(hist_card)

        # ── Presets card ─────────────────────────────────────────────────────
        preset_card = make_card()
        pc_lay = QVBoxLayout(preset_card)
        pc_lay.setContentsMargins(12, 10, 12, 12)
        pc_lay.setSpacing(6)

        prc_hdr = QLabel("Quick Presets")
        prc_hdr.setStyleSheet(
            "color:#A8A5C8; font-family:'Outfit',sans-serif; font-size:10px; "
            "font-weight:600; letter-spacing:1.0px; text-transform:uppercase;"
        )
        pc_lay.addWidget(prc_hdr)

        _PRESETS_ORDER = [
            ("Brain",       "Brain"),
            ("Subdural",    "Subdural"),
            ("Stroke",      "Stroke"),
            ("Bone",        "Bone"),
            ("Soft Tissue", "Soft Tissue"),
            ("Lung",        "Lung"),
            ("Liver",       "Liver"),
        ]
        _PRESET_SS = """
            QPushButton {
                background: rgba(124,58,237,0.07);
                color: #C0BCDC;
                border: 1px solid rgba(124,58,237,0.14);
                border-radius: 7px;
                padding: 6px 10px;
                font-family: 'Outfit', sans-serif;
                font-size: 11px; font-weight: 500;
                text-align: left;
                min-height: 28px;
            }
            QPushButton:hover {
                background: rgba(124,58,237,0.18);
                color: #C4B5FD;
                border-color: rgba(124,58,237,0.45);
            }
            QPushButton:pressed { background: rgba(124,58,237,0.10); }
        """
        from PyQt5.QtWidgets import QHBoxLayout as _HBox
        for i in range(0, len(_PRESETS_ORDER), 2):
            row = _HBox(); row.setSpacing(5)
            for key, label in _PRESETS_ORDER[i:i+2]:
                w_val, c_val = WL_PRESETS[key]
                pbtn = QPushButton(label)
                pbtn.setToolTip(f"W={w_val}  L={c_val}")
                pbtn.setStyleSheet(_PRESET_SS)
                pbtn.setCursor(Qt.PointingHandCursor)
                pbtn.clicked.connect(
                    lambda _c, k=key: self._ctrl.set_window_level(
                        WL_PRESETS[k][0], WL_PRESETS[k][1]
                    )
                )
                row.addWidget(pbtn)
            if len(_PRESETS_ORDER[i:i+2]) < 2:
                row.addStretch()
            pc_lay.addLayout(row)

        right.addWidget(preset_card)
        right.addStretch()
        right_scroll.setWidget(right_inner)
        body.addWidget(right_scroll)

        root.addLayout(body, stretch=1)
        root.addSpacing(12)   # breathing room above nav

        # ── Nav bar (taller, proper symbols) ───────────────────────────────
        nav_card = make_card()
        nav_card.setFixedHeight(68)   # taller so buttons aren't clipped
        nav_lay  = QHBoxLayout(nav_card)
        nav_lay.setContentsMargins(14, 12, 14, 12)   # equal top/bottom padding
        nav_lay.setSpacing(6)

        # Symbols: ⏮ ⏪ ▶/⏸ ⏩ ⏭
        self._btn_first = _nav_btn("|<",  "First frame  (Home)")
        self._btn_prev  = _nav_btn("<<",  "Previous frame  (Left arrow)")
        self._btn_play  = _play_btn()
        self._btn_next  = _nav_btn(">>",  "Next frame  (Right arrow)")
        self._btn_last  = _nav_btn(">|",  "Last frame  (End)")

        self._scrubber  = _scrubber()
        self._frame_lbl = QLabel("—")
        self._frame_lbl.setFixedWidth(60)
        self._frame_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._frame_lbl.setStyleSheet(
            "color:#A8A5C8;font-family:'JetBrains Mono',monospace;font-size:11px;"
        )

        for btn in (self._btn_first, self._btn_prev, self._btn_play,
                    self._btn_next, self._btn_last):
            btn.setEnabled(False)
            nav_lay.addWidget(btn)

        nav_lay.addSpacing(6)
        nav_lay.addWidget(self._scrubber, stretch=1)
        nav_lay.addWidget(self._frame_lbl)

        root.addWidget(nav_card)
        root.addSpacing(10)   # gap before status row

        # ── Status row ─────────────────────────────────────────────────────
        sr = QHBoxLayout(); sr.setContentsMargins(0,0,0,0)
        self._dot = QLabel("●"); self._dot.setStyleSheet("color:#9490B8;font-size:8px;")
        self._status_lbl = QLabel("Ready — load a DICOM file to begin")
        self._status_lbl.setStyleSheet(
            "color:#9490B8;font-family:'JetBrains Mono',monospace;font-size:11px;"
        )
        sr.addWidget(self._dot); sr.addSpacing(7); sr.addWidget(self._status_lbl); sr.addStretch()
        root.addLayout(sr)

        self.setFocusPolicy(Qt.StrongFocus)

    def _connect_signals(self):
        self._btn_load.clicked.connect(self._on_load)
        self._btn_ruler.clicked.connect(self._toggle_ruler)
        self._btn_export.clicked.connect(self._open_export)

        self._btn_play.clicked.connect(self._toggle_play)
        self._btn_first.clicked.connect(lambda: self._ctrl.seek_frame(0))
        self._btn_last.clicked.connect(lambda: self._ctrl.seek_frame(self._ctrl.frame_count - 1))
        self._btn_prev.clicked.connect(lambda: self._ctrl.step_frame(-1))
        self._btn_next.clicked.connect(lambda: self._ctrl.step_frame(1))
        self._scrubber.valueChanged.connect(self._on_scrubber)

        self._ctrl.file_loaded.connect(self._on_file_loaded)
        self._ctrl.image_ready.connect(self._show_array)
        self._ctrl.frame_ready.connect(self._show_frame)

        self._ctrl.playback_stopped.connect(self._on_stopped)
        self._ctrl.status_message.connect(self._on_status)

        # W/L panel → controller (panel is the source, fires debounced)
        # W/L panel → controller  (panel emits debounced wl_changed)
        self._wl_panel.wl_changed.connect(self._ctrl.set_window_level)

        # Controller → panel  (set_wl uses blockSignals, never re-emits)
        self._ctrl.wl_changed.connect(self._wl_panel.set_wl)
        self._ctrl.wl_changed.connect(self._hist_panel.update_wl_band)

        # Histogram data → histogram panel
        self._ctrl.histogram_ready.connect(self._hist_panel.update_histogram)

        # Canvas update from W/L rerender — direct connection, no hasattr
        self._ctrl.wl_render_ready.connect(self._show_wl_rerender)

        # Histogram click → snap brightness center
        self._hist_panel.wl_snap_requested = (
            lambda c: self._ctrl.set_window_level(self._ctrl.wl_width, c)
        )

        self._cmap_bar.lut_changed.connect(self._on_lut_changed)
        self._canvas.measurement_added.connect(self._fwd_measurement_added)
        self._canvas.measurement_cleared.connect(self._fwd_measurements_cleared)

    # ── Keyboard ───────────────────────────────────────────────────────────────

    def keyPressEvent(self, ev):
        if not self._ctrl.is_loaded:
            return super().keyPressEvent(ev)
        k = ev.key()
        if   k == Qt.Key_Space: self._toggle_play()
        elif k == Qt.Key_Right: self._ctrl.step_frame(1)
        elif k == Qt.Key_Left:  self._ctrl.step_frame(-1)
        elif k == Qt.Key_Home:  self._ctrl.seek_frame(0)
        elif k == Qt.Key_End:   self._ctrl.seek_frame(self._ctrl.frame_count - 1)
        else: super().keyPressEvent(ev)

    # ── Slots ──────────────────────────────────────────────────────────────────

    def _on_load(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open DICOM File", "", "DICOM Files (*.dcm);;All Files (*)"
        )
        if path: self._ctrl.load_file(path)

    def _on_file_loaded(self, path: str):
        self._all_rendered.clear(); self._frame_idx = 0

        ds = getattr(self._ctrl, "_model", None)
        if ds and hasattr(ds, "dataset") and ds.dataset:
            ps = getattr(ds.dataset, "PixelSpacing", None)
            if ps and len(ps) >= 2:
                try: self._canvas.set_pixel_spacing(float(ps[0]), float(ps[1]))
                except Exception: pass

        is_multi = self._ctrl.is_multiframe
        n        = self._ctrl.frame_count

        self._scrubber_lock = True
        self._scrubber.setRange(0, max(0, n - 1))
        self._scrubber.setValue(0)
        self._scrubber_lock = False
        self._frame_lbl.setText(f"1 / {n}" if is_multi else "—")

        for btn in (self._btn_first, self._btn_prev, self._btn_play,
                    self._btn_next, self._btn_last):
            btn.setEnabled(is_multi)

        self._btn_ruler.setEnabled(True)
        self._btn_export.setEnabled(True)
        self._set_play_icon(False)

        short = path.replace("\\", "/").split("/")[-1]
        self._set_status(f"{short}  ·  ready", "#10B981")
        self._ctrl.display_image()

    def _show_array(self, arr: np.ndarray):
        self._last_gray    = arr
        self._all_rendered = [arr]
        self._render_with_lut(arr)
        self._frame_lbl.setText("—")
        self._set_status("Image displayed", "#10B981")

    def _show_frame(self, arr: np.ndarray):
        self._last_gray = arr
        self._render_with_lut(arr)

        idx = self._ctrl.current_frame_index
        n   = self._ctrl.frame_count

        # Always sync the label and scrubber — scrubber_lock prevents
        # the valueChanged from triggering seek_frame again
        self._frame_idx = idx
        self._frame_lbl.setText(f"{idx + 1} / {n}")
        self._scrubber_lock = True
        self._scrubber.setValue(idx)
        self._scrubber_lock = False

        # Collect frames for GIF export
        if idx >= len(self._all_rendered):
            self._all_rendered.append(arr)
        else:
            self._all_rendered[idx] = arr

        self._set_play_icon(self._ctrl.is_playing)

    def _show_wl_rerender(self, arr: np.ndarray):
        """Handle W/L rerender — updates canvas ONLY, never touches frame state."""
        self._last_gray = arr
        self._render_with_lut(arr)
        if self._frame_idx < len(self._all_rendered):
            self._all_rendered[self._frame_idx] = arr

    def _on_stopped(self):
        self._set_play_icon(False)
        n = self._ctrl.frame_count
        i = self._ctrl.current_frame_index
        self._set_status(f"Paused  ·  frame {i+1} / {n}", "#C0BCDC")

    def _on_status(self, msg: str):
        if any(w in msg.lower() for w in ("error","fail")):
            self._set_status(msg, "#FF6B6B")
        elif any(w in msg.lower() for w in ("loaded","success","displayed","series")):
            self._set_status(msg, "#10B981")
        else:
            self._set_status(msg, "#C0BCDC")

    def _toggle_play(self):
        if not self._ctrl.is_multiframe: return
        if self._ctrl.is_playing:
            self._ctrl.pause_playback(); self._set_play_icon(False)
        else:
            self._ctrl.resume_playback(); self._set_play_icon(True)

    def _set_play_icon(self, playing: bool):
        self._btn_play.setText("||" if playing else ">")
        self._btn_play.setToolTip("Pause  (Space)" if playing else "Play  (Space)")  # noqa

    def _on_scrubber(self, value: int):
        if self._scrubber_lock: return
        if self._ctrl.is_multiframe:
            self._ctrl.seek_frame(value)

    def _on_lut_changed(self, name: str):
        self._active_lut = name
        if self._last_gray is not None:
            self._render_with_lut(self._last_gray)

    def _toggle_ruler(self, checked: bool):
        self._canvas.set_ruler_mode(checked)
        if checked:
            self._btn_ruler.setStyleSheet("""
                QPushButton {
                    background:rgba(124,58,237,0.30);color:#C4B5FD;
                    border:1px solid rgba(124,58,237,0.65);border-radius:8px;
                    padding:8px 18px;font-size:12px;font-weight:600;min-height:34px;
                }
            """)
            self._set_status("Ruler active — drag on the image to measure", "#A78BFA")
        else:
            self._btn_ruler.setStyleSheet("")

    # ── Measurement forwarding (routed to sidebar via main_window) ─────────────

    def _fwd_measurement_added(self, label: str):
        if callable(self.on_measurement_added):
            self.on_measurement_added(label)

    def _fwd_measurements_cleared(self):
        if callable(self.on_measurements_cleared):
            self.on_measurements_cleared()

    def clear_measurements(self):
        self._canvas.clear_measurements()

    # ── Export ─────────────────────────────────────────────────────────────────

    def _open_export(self):
        export_arr = None
        if self._last_gray is not None:
            export_arr = (self._last_gray if self._active_lut == "Grayscale"
                          else apply_lut(self._last_gray, self._active_lut))
        gif_frames = [
            (f if self._active_lut == "Grayscale"
             else apply_lut(f, self._active_lut)[:, :, :3])
            for f in self._all_rendered
        ]
        tags = []
        try: tags = self._ctrl._model.get_all_tags()
        except Exception: pass
        ExportDialog(current_arr=export_arr, all_frames=gif_frames,
                     tags=tags, is_multiframe=self._ctrl.is_multiframe,
                     parent=self).exec_()

    # ── Render ─────────────────────────────────────────────────────────────────

    def _render_with_lut(self, gray: np.ndarray):
        if self._active_lut == "Grayscale":
            px = ndarray_to_pixmap(gray)
        else:
            rgba = np.ascontiguousarray(apply_lut(gray, self._active_lut))
            h, w = rgba.shape[:2]
            img  = QImage(rgba.data, w, h, w*4, QImage.Format_RGBA8888)
            img._ref = rgba
            px   = QPixmap.fromImage(img)
        self._canvas.set_pixmap(px)

    def _set_status(self, msg: str, color: str = "#C0BCDC"):
        self._dot.setStyleSheet(f"color:{color};font-size:8px;")
        self._status_lbl.setStyleSheet(
            f"color:{color};font-family:'JetBrains Mono',monospace;font-size:11px;"
        )
        self._status_lbl.setText(msg)
