"""app/gui/threed_tab.py — 3D Tile Viewer, Deep Space Medical theme."""

from __future__ import annotations

from typing import List

import numpy as np
from PyQt5.QtCore import QRectF, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.gui.widgets import make_button
from config.settings import TILE_COLUMNS, TILE_HEIGHT, TILE_PADDING, TILE_WIDTH


class TileViewerTab(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._ctrl = controller
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 14)
        root.setSpacing(0)

        tb = QHBoxLayout()
        tb.setSpacing(8)
        tb.setContentsMargins(0, 0, 0, 16)
        self._btn_tiles = make_button("🔲  Display Tiles", "primary", enabled=False, min_width=130)
        self._btn_zoom_in = make_button("＋", min_width=38, tooltip="Zoom in")
        self._btn_zoom_out = make_button("－", min_width=38, tooltip="Zoom out")
        self._btn_reset = make_button("↺  Reset", min_width=80, tooltip="Fit first row")
        self._info = QLabel("")
        self._info.setStyleSheet(
            "color:#2D2A45; font-family:'JetBrains Mono',monospace; font-size:11px;"
        )
        tb.addWidget(self._btn_tiles)
        tb.addSpacing(10)
        tb.addWidget(self._btn_zoom_in)
        tb.addWidget(self._btn_zoom_out)
        tb.addWidget(self._btn_reset)
        tb.addStretch()
        tb.addWidget(self._info)
        root.addLayout(tb)

        self._scene = QGraphicsScene(self)
        self._view = QGraphicsView(self._scene, self)
        self._view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self._view.setDragMode(QGraphicsView.ScrollHandDrag)
        self._view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self._view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._empty = QLabel(
            '<div style="text-align:center;">'
            '<p style="color:#2D2A45;font-size:32px;margin:0;">⬡</p>'
            "<p style=\"color:#2D2A45;font-family:'Outfit',sans-serif;"
            'font-size:13px;letter-spacing:2px;margin:10px 0 0;">LOAD FILE · PRESS DISPLAY TILES</p>'
            "</div>"
        )
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._empty.setStyleSheet(
            "background:#07050F; border-radius:12px; border:1px solid rgba(124,58,237,0.10);"
        )

        root.addWidget(self._empty, stretch=1)
        root.addWidget(self._view, stretch=1)
        self._view.setVisible(False)

    def _connect_signals(self):
        self._btn_tiles.clicked.connect(self._on_display)
        self._btn_zoom_in.clicked.connect(lambda: self._view.scale(1.25, 1.25))
        self._btn_zoom_out.clicked.connect(lambda: self._view.scale(0.80, 0.80))
        self._btn_reset.clicked.connect(lambda: QTimer.singleShot(0, self._fit_view))
        self._ctrl.file_loaded.connect(lambda _: self._btn_tiles.setEnabled(True))

    def _on_display(self):
        frames, label = self._ctrl.get_tile_frames()
        if not frames:
            self._info.setText("No frames found")
            return
        self._render(frames)
        self._info.setText(f"{len(frames)} slices")
        self._empty.setVisible(False)
        self._view.setVisible(True)
        QTimer.singleShot(0, self._fit_view)

    def _render(self, frames: List[np.ndarray]):
        self._scene.clear()
        cols = TILE_COLUMNS
        tw = TILE_WIDTH
        th = TILE_HEIGHT
        pad = TILE_PADDING
        total = len(frames)
        rows = (total + cols - 1) // cols

        for i, arr in enumerate(frames):
            if arr.ndim != 2:
                arr = arr.squeeze()
            if arr.ndim != 2:
                continue
            qimg = QImage(
                arr.data, arr.shape[1], arr.shape[0], arr.shape[1], QImage.Format_Grayscale8
            ).scaled(tw, th, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            item = QGraphicsPixmapItem(QPixmap.fromImage(qimg))
            r, c = divmod(i, cols)
            item.setPos(c * (tw + pad), r * (th + pad))
            item.setToolTip(f"Slice {i}")
            self._scene.addItem(item)
            txt = self._scene.addText(f"{i}", QFont("JetBrains Mono", 7))
            txt.setDefaultTextColor(QColor("#2D2A45"))
            txt.setPos(c * (tw + pad) + 4, r * (th + pad) + th + 2)

        self._scene.setSceneRect(0, 0, cols * (tw + pad), rows * (th + pad + 18))

    def _fit_view(self):
        if not self._scene.sceneRect().isValid():
            return
        first_row = QRectF(
            0, 0, TILE_COLUMNS * (TILE_WIDTH + TILE_PADDING), TILE_HEIGHT + TILE_PADDING + 20
        )
        self._view.fitInView(first_row, Qt.KeepAspectRatio)
