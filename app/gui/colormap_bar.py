"""
app/gui/colormap_bar.py
=======================
Compact colormap / LUT selector bar — sits below the toolbar in the image tab.

Shows a row of clickable LUT swatches with names. The active one is
highlighted. Emits lut_changed(name: str) when the user picks a new one.
"""

from __future__ import annotations

import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.logic.colormap import LUT_NAMES, lut_preview_strip

_SWATCH_W = 64
_SWATCH_H = 10


def _strip_pixmap(lut_name: str) -> QPixmap:
    rgba = lut_preview_strip(lut_name, width=_SWATCH_W, height=_SWATCH_H)
    rgba = np.ascontiguousarray(rgba)
    h, w = rgba.shape[:2]
    img = QImage(rgba.data, w, h, w * 4, QImage.Format_RGBA8888)
    img._ref = rgba  # prevent GC
    return QPixmap.fromImage(img)


class _LutChip(QWidget):
    """Single LUT chip: swatch + label, toggleable."""

    clicked = pyqtSignal(str)

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self._name = name
        self._active = False
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(f"Apply {name} colourmap")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignCenter)

        # Swatch
        swatch = QLabel()
        swatch.setFixedSize(_SWATCH_W, _SWATCH_H)
        swatch.setPixmap(_strip_pixmap(name))
        swatch.setStyleSheet("border-radius:3px;")
        lay.addWidget(swatch, alignment=Qt.AlignCenter)

        # Name label
        self._lbl = QLabel(name)
        self._lbl.setAlignment(Qt.AlignCenter)
        self._lbl.setStyleSheet(
            "color:#3D3860; font-family:'Outfit',sans-serif; " "font-size:10px; font-weight:500;"
        )
        lay.addWidget(self._lbl)

        self._apply_style(False)

    def _apply_style(self, active: bool):
        if active:
            self.setStyleSheet("""
                QWidget {
                    background: rgba(124,58,237,0.18);
                    border: 1px solid rgba(124,58,237,0.50);
                    border-radius: 8px;
                }
            """)
            self._lbl.setStyleSheet(
                "color:#C4B5FD; font-family:'Outfit',sans-serif; "
                "font-size:10px; font-weight:600;"
            )
        else:
            self.setStyleSheet("""
                QWidget {
                    background: rgba(255,255,255,0.025);
                    border: 1px solid rgba(124,58,237,0.10);
                    border-radius: 8px;
                }
                QWidget:hover {
                    background: rgba(124,58,237,0.09);
                    border-color: rgba(124,58,237,0.28);
                }
            """)
            self._lbl.setStyleSheet(
                "color:#3D3860; font-family:'Outfit',sans-serif; "
                "font-size:10px; font-weight:500;"
            )

    def set_active(self, v: bool):
        self._active = v
        self._apply_style(v)

    def mousePressEvent(self, _):
        self.clicked.emit(self._name)


class ColormapBar(QWidget):
    """
    Horizontal scrollable row of LUT chips.

    Signals
    -------
    lut_changed(str)
        Name of the newly selected LUT.
    """

    lut_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_name = "Grayscale"
        self._chips: dict[str, _LutChip] = {}
        self._setup_ui()

    def _setup_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        # Label
        lbl = QLabel("Colormap")
        lbl.setStyleSheet(
            "color:#3D3860; font-family:'Outfit',sans-serif; "
            "font-size:10px; font-weight:600; letter-spacing:0.8px;"
        )
        lbl.setFixedWidth(68)
        outer.addWidget(lbl)

        # Scrollable chip row
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        scroll.setFixedHeight(52)

        container = QWidget()
        container.setStyleSheet("background:transparent;")
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(5)

        for name in LUT_NAMES:
            chip = _LutChip(name)
            chip.clicked.connect(self._on_chip_clicked)
            chip.setFixedSize(76, 46)
            self._chips[name] = chip
            row.addWidget(chip)
        row.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll, stretch=1)

        # Set initial active
        self._chips["Grayscale"].set_active(True)

    def _on_chip_clicked(self, name: str):
        if name == self._active_name:
            return
        self._chips[self._active_name].set_active(False)
        self._chips[name].set_active(True)
        self._active_name = name
        self.lut_changed.emit(name)

    @property
    def active_lut(self) -> str:
        return self._active_name
