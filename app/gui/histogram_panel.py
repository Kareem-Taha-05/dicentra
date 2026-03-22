"""
app/gui/histogram_panel.py
==========================
Live HU histogram panel.

The ONLY output this widget produces is wl_snap_requested — and only when
the user explicitly clicks the histogram canvas. It never fires automatically.
"""

from __future__ import annotations

import matplotlib
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

matplotlib.use("Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

_BG = "#07050F"
_BAR = "#2D1F5E"
_ACC = "#7C3AED"
_CTR = "#F59E0B"


class HistogramPanel(QWidget):
    """
    Displays a log-scale HU histogram with a W/L overlay band.

    Public methods
    --------------
    update_histogram(counts, edges)   — called when a new frame is loaded
    update_wl_band(width, center)     — called when W/L changes (visual only)

    Callback (set externally, not a Qt signal)
    ------------------------------------------
    wl_snap_requested(center: float)
        Called ONLY when the user explicitly clicks the histogram.
        Default is a no-op. Set by image_tab after construction.
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._wl_width = 400.0
        self._wl_center = 40.0
        self._counts = None
        self._edges = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 10)
        root.setSpacing(6)

        hdr = QLabel("Pixel Distribution")
        hdr.setStyleSheet(
            "color:#B0ADCC; font-family:'Outfit',sans-serif; "
            "font-size:10px; font-weight:600; letter-spacing:1.2px; "
            "text-transform:uppercase;"
        )
        root.addWidget(hdr)

        self._fig = Figure(figsize=(2.8, 1.6), dpi=96)
        self._fig.patch.set_facecolor(_BG)
        self._ax = self._fig.add_subplot(111)
        self._style_ax()

        self._canvas = FigureCanvas(self._fig)
        self._canvas.setStyleSheet(f"background:{_BG};")
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._canvas.setFixedHeight(148)
        # Click only — no drag, no auto-fire
        self._canvas.mpl_connect("button_press_event", self._on_click)
        root.addWidget(self._canvas)

        hint = QLabel("click histogram  →  snap brightness center")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color:#9490B8; font-family:'JetBrains Mono',monospace; font-size:9px;")
        root.addWidget(hint)

    # ── axis styling ───────────────────────────────────────────────────────────

    def _style_ax(self) -> None:
        ax = self._ax
        ax.set_facecolor(_BG)
        ax.tick_params(colors="#9490B8", labelsize=7, length=2, width=0.5)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.yaxis.set_visible(False)
        self._fig.tight_layout(pad=0.3)

    # ── public update methods ─────────────────────────────────────────────────

    def update_histogram(self, counts: np.ndarray, edges: np.ndarray) -> None:
        """Receive new histogram data (called when frame changes)."""
        self._counts = counts
        self._edges = edges
        self._redraw()

    def update_wl_band(self, width: float, center: float) -> None:
        """Update the W/L overlay band (called when sliders move)."""
        self._wl_width = float(width)
        self._wl_center = float(center)
        self._redraw()

    # ── drawing ────────────────────────────────────────────────────────────────

    def _redraw(self) -> None:
        self._ax.cla()
        self._style_ax()

        if self._counts is None:
            self._canvas.draw_idle()
            return

        bc = (self._edges[:-1] + self._edges[1:]) / 2.0
        lc = np.log1p(self._counts.astype(float))
        bw = (self._edges[1] - self._edges[0]) * 0.85

        self._ax.bar(bc, lc, width=bw, color=_BAR, linewidth=0, zorder=2)

        lo = self._wl_center - self._wl_width / 2.0
        hi = self._wl_center + self._wl_width / 2.0
        self._ax.axvspan(lo, hi, alpha=0.22, color=_ACC, linewidth=0, zorder=3)
        self._ax.axvline(
            self._wl_center,
            color=_CTR,
            linewidth=1.4,
            alpha=0.85,
            linestyle="--",
            zorder=4,
        )

        self._ax.set_xlim(self._edges[0], self._edges[-1])
        self._ax.set_ylim(0, max(lc.max() * 1.10, 1))

        self._ax.set_xticks([lo, self._wl_center, hi])
        self._ax.set_xticklabels(
            [f"{int(lo)}", f"{int(self._wl_center)}", f"{int(hi)}"],
            color="#A8A5C8",
            fontsize=7,
        )

        self._fig.tight_layout(pad=0.3)
        self._canvas.draw_idle()

    # ── user interaction ───────────────────────────────────────────────────────

    def _on_click(self, ev) -> None:
        """User clicked the histogram — snap W/L center to clicked HU value."""
        if ev.inaxes != self._ax or ev.xdata is None:
            return
        self.wl_snap_requested(float(ev.xdata))

    # Callback — replaced by image_tab after construction
    def wl_snap_requested(self, center: float) -> None:  # noqa: D401
        """Override / replace this to handle histogram clicks."""
        pass
