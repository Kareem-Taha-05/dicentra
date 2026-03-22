"""
app/gui/wl_panel.py
===================
Window / Level control panel — completely self-contained.

Design rules that make this bug-free:
  1. wl_changed is emitted ONLY by _emit_wl() (debounced slider) and
     _on_preset() (direct click). NEVER by set_wl().
  2. set_wl() is the "receive external update" path — it sets controls
     silently using blockSignals on every widget, so nothing re-emits.
  3. _building flag is kept as a secondary guard but blockSignals is the
     primary protection so there are zero timing-dependent race conditions.
"""

from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config.settings import WL_DEFAULT_CENTER, WL_DEFAULT_WIDTH, WL_PRESETS

_W_MIN, _W_MAX = 1, 4000
_C_MIN, _C_MAX = -1500, 1500

_PRESETS = [
    ("Brain", "🧠", "Soft brain tissue"),
    ("Bone", "🦴", "Cortical bone"),
    ("Lung", "🫁", "Airway & parenchyma"),
    ("Soft Tissue", "🫀", "General abdomen"),
    ("Stroke", "⚡", "Early ischaemia"),
    ("Liver", "🔴", "Hepatic parenchyma"),
    ("Subdural", "💡", "Blood / fluid layers"),
]


# ── widget factories ───────────────────────────────────────────────────────────


def _make_slider(mn: int, mx: int, val: int) -> QSlider:
    s = QSlider(Qt.Horizontal)
    s.setRange(mn, mx)
    s.setValue(val)
    s.setMinimumHeight(26)
    s.setStyleSheet("""
        QSlider::groove:horizontal {
            height: 5px;
            background: rgba(124,58,237,0.14);
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            width: 22px; height: 22px; border-radius: 11px;
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #A78BFA, stop:1 #7C3AED);
            margin: -9px 0;
            border: 2px solid rgba(196,181,253,0.55);
        }
        QSlider::handle:horizontal:hover {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #C4B5FD, stop:1 #9F67FF);
            border-color: rgba(196,181,253,0.90);
        }
        QSlider::sub-page:horizontal {
            background: rgba(124,58,237,0.42);
            border-radius: 3px;
        }
    """)
    return s


def _make_spinbox(mn: int, mx: int, val: int, step: int = 1, color: str = "#F59E0B") -> QSpinBox:
    sb = QSpinBox()
    sb.setRange(mn, mx)
    sb.setValue(val)
    sb.setSingleStep(step)
    sb.setFixedWidth(74)
    sb.setAlignment(Qt.AlignCenter)
    sb.setStyleSheet(f"""
        QSpinBox {{
            background: #1C1830;
            color: {color};
            border: 1px solid rgba(124,58,237,0.28);
            border-radius: 7px;
            padding: 5px 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            font-weight: 500;
        }}
        QSpinBox:focus {{ border-color: rgba(124,58,237,0.65); }}
        QSpinBox::up-button, QSpinBox::down-button {{ width: 0; border: none; }}
    """)
    return sb


def _row_label(title: str, subtitle: str) -> QWidget:
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(1)
    t = QLabel(title)
    t.setStyleSheet(
        "color:#A78BFA; font-family:'Outfit',sans-serif; " "font-size:12px; font-weight:600;"
    )
    s = QLabel(subtitle)
    s.setStyleSheet("color:#A8A5C8; font-family:'Outfit',sans-serif; font-size:10px;")
    lay.addWidget(t)
    lay.addWidget(s)
    return w


# ── panel ──────────────────────────────────────────────────────────────────────


class WLPanel(QWidget):
    """
    Self-contained Window / Level panel.

    Signals
    -------
    wl_changed(width, center)
        Fired (debounced 60 ms) when the user moves a slider.
        Also fired immediately when a preset is clicked.
        NEVER fired by set_wl().
    """

    wl_changed = pyqtSignal(float, float)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._building = False  # True only while set_wl / preset is writing

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(60)
        self._debounce.timeout.connect(self._fire)

        self._build()

    # ── build ──────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 16)
        root.setSpacing(12)

        # ── header ─────────────────────────────────────────────────────────
        hdr = QLabel("Window / Level")
        hdr.setStyleSheet(
            "color:#C8C5E8; font-family:'Outfit',sans-serif; font-size:11px; "
            "font-weight:600; letter-spacing:1.2px; text-transform:uppercase; "
            "padding-bottom:8px; border-bottom:1px solid rgba(124,58,237,0.14);"
        )
        root.addWidget(hdr)

        # ── W (contrast) ────────────────────────────────────────────────────
        root.addWidget(_row_label("W — Contrast", "Narrow = sharp  ·  Wide = soft"))

        self._w_slider = _make_slider(_W_MIN, _W_MAX, int(WL_DEFAULT_WIDTH))
        self._w_spin = _make_spinbox(
            _W_MIN, _W_MAX, int(WL_DEFAULT_WIDTH), step=10, color="#F59E0B"
        )
        w_row = QHBoxLayout()
        w_row.setSpacing(8)
        w_row.addWidget(self._w_slider, stretch=1)
        w_row.addWidget(self._w_spin)
        root.addLayout(w_row)

        # ── L (brightness) ──────────────────────────────────────────────────
        root.addWidget(_row_label("L — Level", "Left = brighter  ·  Right = darker"))

        self._c_slider = _make_slider(_C_MIN, _C_MAX, int(WL_DEFAULT_CENTER))
        self._c_spin = _make_spinbox(
            _C_MIN, _C_MAX, int(WL_DEFAULT_CENTER), step=5, color="#A78BFA"
        )
        c_row = QHBoxLayout()
        c_row.setSpacing(8)
        c_row.addWidget(self._c_slider, stretch=1)
        c_row.addWidget(self._c_spin)
        root.addLayout(c_row)

        # ── HU range display ────────────────────────────────────────────────
        rng_row = QHBoxLayout()
        rng_row.setSpacing(4)
        self._lbl_lo = QLabel("")
        self._lbl_hi = QLabel("")
        lbl_mid = QLabel("visible HU range")
        for lbl in (self._lbl_lo, self._lbl_hi):
            lbl.setStyleSheet(
                "color:#B0ADCC; font-family:'JetBrains Mono',monospace; font-size:10px;"
            )
        lbl_mid.setStyleSheet("color:#9490B8; font-family:'Outfit',sans-serif; font-size:10px;")
        rng_row.addWidget(self._lbl_lo)
        rng_row.addStretch()
        rng_row.addWidget(lbl_mid)
        rng_row.addStretch()
        rng_row.addWidget(self._lbl_hi)
        root.addLayout(rng_row)
        self._refresh_range()

        # ── wire slider / spinbox pairs ──────────────────────────────────────
        self._w_slider.valueChanged.connect(self._w_slider_moved)
        self._c_slider.valueChanged.connect(self._c_slider_moved)
        self._w_spin.valueChanged.connect(self._w_spin_changed)
        self._c_spin.valueChanged.connect(self._c_spin_changed)

    # ── internal slots ─────────────────────────────────────────────────────────

    def _w_slider_moved(self, v: int) -> None:
        if self._building:
            return
        self._w_spin.blockSignals(True)
        self._w_spin.setValue(v)
        self._w_spin.blockSignals(False)
        self._refresh_range()
        self._debounce.start()

    def _c_slider_moved(self, v: int) -> None:
        if self._building:
            return
        self._c_spin.blockSignals(True)
        self._c_spin.setValue(v)
        self._c_spin.blockSignals(False)
        self._refresh_range()
        self._debounce.start()

    def _w_spin_changed(self, v: int) -> None:
        if self._building:
            return
        self._w_slider.blockSignals(True)
        self._w_slider.setValue(v)
        self._w_slider.blockSignals(False)
        self._refresh_range()
        self._debounce.start()

    def _c_spin_changed(self, v: int) -> None:
        if self._building:
            return
        self._c_slider.blockSignals(True)
        self._c_slider.setValue(v)
        self._c_slider.blockSignals(False)
        self._refresh_range()
        self._debounce.start()

    def _on_preset(self, name: str) -> None:
        w, c = WL_PRESETS[name]
        self._building = True
        self._w_slider.blockSignals(True)
        self._w_slider.setValue(int(w))
        self._w_slider.blockSignals(False)
        self._c_slider.blockSignals(True)
        self._c_slider.setValue(int(c))
        self._c_slider.blockSignals(False)
        self._w_spin.blockSignals(True)
        self._w_spin.setValue(int(w))
        self._w_spin.blockSignals(False)
        self._c_spin.blockSignals(True)
        self._c_spin.setValue(int(c))
        self._c_spin.blockSignals(False)
        self._building = False
        self._refresh_range()
        self._debounce.stop()  # cancel any pending drag emit
        self.wl_changed.emit(float(w), float(c))  # fire immediately

    def _fire(self) -> None:
        """Called by debounce timer — emit current slider values."""
        self.wl_changed.emit(
            float(self._w_slider.value()),
            float(self._c_slider.value()),
        )

    def _refresh_range(self) -> None:
        w = self._w_slider.value()
        c = self._c_slider.value()
        self._lbl_lo.setText(f"{c - w // 2} HU")
        self._lbl_hi.setText(f"{c + w // 2} HU")

    # ── public API ─────────────────────────────────────────────────────────────

    def set_wl(self, width: float, center: float) -> None:
        """
        Update controls from an external source (e.g. controller feedback).
        Uses blockSignals on every widget — NEVER emits wl_changed.
        """
        self._building = True
        w = int(max(_W_MIN, min(_W_MAX, width)))
        c = int(max(_C_MIN, min(_C_MAX, center)))
        self._w_slider.blockSignals(True)
        self._w_slider.setValue(w)
        self._w_slider.blockSignals(False)
        self._c_slider.blockSignals(True)
        self._c_slider.setValue(c)
        self._c_slider.blockSignals(False)
        self._w_spin.blockSignals(True)
        self._w_spin.setValue(w)
        self._w_spin.blockSignals(False)
        self._c_spin.blockSignals(True)
        self._c_spin.setValue(c)
        self._c_spin.blockSignals(False)
        self._building = False
        self._refresh_range()

    @property
    def width_value(self) -> float:
        return float(self._w_slider.value())

    @property
    def center_value(self) -> float:
        return float(self._c_slider.value())
