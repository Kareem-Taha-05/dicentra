"""
app/gui/ruler_canvas.py
=======================
Image display canvas with an interactive measurement ruler.

Replaces the plain QLabel canvas in image_tab.py.

Features
--------
- Displays any uint8 (H,W) or (H,W,4) array, scaled to fit
- Ruler mode: click-drag draws a line; release shows distance in mm
  (uses PixelSpacing DICOM tag; falls back to px if not available)
- Multiple measurements persist until "Clear" is clicked
- Crosshair overlay shows pixel coordinates on hover
- Escape key cancels a measurement in progress
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from PyQt5.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt5.QtWidgets import QSizePolicy, QWidget

# ── Data types ─────────────────────────────────────────────────────────────────


class _Measurement:
    """One ruler line with computed distance."""

    def __init__(self, p1: QPointF, p2: QPointF, px_dist: float, mm_dist: Optional[float]):
        self.p1 = p1
        self.p2 = p2
        self.px_dist = px_dist
        self.mm_dist = mm_dist

    @property
    def label(self) -> str:
        if self.mm_dist is not None:
            return f"{self.mm_dist:.1f} mm"
        return f"{self.px_dist:.0f} px"


# ── Canvas ─────────────────────────────────────────────────────────────────────


class RulerCanvas(QWidget):
    """
    Interactive image canvas with ruler overlay.

    Public API
    ----------
    set_pixmap(pixmap)      — replace the displayed image
    set_pixel_spacing(sy, sx) — provide mm/px factors (from PixelSpacing tag)
    set_ruler_mode(bool)    — enable / disable ruler drawing
    clear_measurements()    — remove all ruler lines
    measurement_count       — property: number of stored measurements
    """

    measurement_added = pyqtSignal(str)  # label of the new measurement
    measurement_cleared = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(460, 460)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self._pixmap: Optional[QPixmap] = None
        self._measurements: List[_Measurement] = []
        self._drawing: bool = False
        self._start_img: Optional[QPointF] = None  # in image coords
        self._end_img: Optional[QPointF] = None
        self._hover_img: Optional[QPointF] = None
        self._ruler_mode: bool = False
        self._pixel_spacing: Tuple[float, float] = (1.0, 1.0)  # (row_mm, col_mm)
        self._img_rect: QRectF = QRectF()

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_pixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.update()

    def set_pixel_spacing(self, row_mm: float, col_mm: float):
        """Call with values from DICOM PixelSpacing tag (in mm per pixel)."""
        self._pixel_spacing = (row_mm, col_mm)

    def set_ruler_mode(self, enabled: bool):
        self._ruler_mode = enabled
        if enabled:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            self._drawing = False
            self._start_img = None
            self._end_img = None
        self.update()

    def clear_measurements(self):
        self._measurements.clear()
        self._drawing = False
        self._start_img = None
        self.update()
        self.measurement_cleared.emit()

    @property
    def measurement_count(self) -> int:
        return len(self._measurements)

    # ── Coordinate helpers ─────────────────────────────────────────────────────

    def _widget_to_image(self, wp: QPointF) -> Optional[QPointF]:
        """Convert widget-space point to image-space point."""
        if self._img_rect.isEmpty():
            return None
        ix = (wp.x() - self._img_rect.x()) / self._img_rect.width()
        iy = (wp.y() - self._img_rect.y()) / self._img_rect.height()
        return QPointF(ix, iy)  # normalised [0,1]

    def _image_to_widget(self, ip: QPointF) -> QPointF:
        return QPointF(
            self._img_rect.x() + ip.x() * self._img_rect.width(),
            self._img_rect.y() + ip.y() * self._img_rect.height(),
        )

    def _px_distance(self, a: QPointF, b: QPointF) -> Tuple[float, Optional[float]]:
        """
        Return (pixel_distance, mm_distance_or_None).
        a and b are in normalised image coords [0,1].
        We need the actual pixel dimensions of the original image to convert.
        """
        if self._pixmap is None:
            return 0.0, None
        W = self._pixmap.width()
        H = self._pixmap.height()
        dx_px = (b.x() - a.x()) * W
        dy_px = (b.y() - a.y()) * H
        px_d = math.hypot(dx_px, dy_px)

        ry, rx = self._pixel_spacing
        if ry > 0 and rx > 0:
            mm_d = math.hypot(dx_px * rx, dy_px * ry)
            return px_d, mm_d
        return px_d, None

    # ── Events ─────────────────────────────────────────────────────────────────

    def mousePressEvent(self, ev):
        if not self._ruler_mode or ev.button() != Qt.LeftButton:
            return
        ip = self._widget_to_image(QPointF(ev.pos()))
        if ip:
            self._drawing = True
            self._start_img = ip
            self._end_img = ip

    def mouseMoveEvent(self, ev):
        ip = self._widget_to_image(QPointF(ev.pos()))
        if ip:
            self._hover_img = ip
            if self._drawing:
                self._end_img = ip
        self.update()

    def mouseReleaseEvent(self, ev):
        if not self._ruler_mode or not self._drawing:
            return
        if ev.button() != Qt.LeftButton:
            return
        ip = self._widget_to_image(QPointF(ev.pos()))
        if ip and self._start_img:
            self._end_img = ip
            px_d, mm_d = self._px_distance(self._start_img, ip)
            if px_d > 3:  # ignore tiny accidental clicks
                m = _Measurement(self._start_img, ip, px_d, mm_d)
                self._measurements.append(m)
                self.measurement_added.emit(m.label)
        self._drawing = False
        self._start_img = None
        self._end_img = None
        self.update()

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape and self._drawing:
            self._drawing = False
            self._start_img = None
            self._end_img = None
            self.update()

    def leaveEvent(self, _):
        self._hover_img = None
        self.update()

    # ── Paint ──────────────────────────────────────────────────────────────────

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        W, H = self.width(), self.height()

        # Background
        p.fillRect(0, 0, W, H, QColor("#07050F"))

        # Image
        if self._pixmap:
            pm = self._pixmap
            aspect = pm.width() / pm.height()
            if W / H > aspect:
                dh = H
                dw = int(dh * aspect)
            else:
                dw = W
                dh = int(dw / aspect)
            ox = (W - dw) // 2
            oy = (H - dh) // 2
            self._img_rect = QRectF(ox, oy, dw, dh)
            p.drawPixmap(int(ox), int(oy), dw, dh, pm)
        else:
            self._img_rect = QRectF()
            p.setPen(QColor("#2D2A45"))
            p.setFont(QFont("Outfit", 13))
            p.drawText(self.rect(), Qt.AlignCenter, "NO IMAGE LOADED")

        # ── Ruler overlays ─────────────────────────────────────────────────
        if not self._img_rect.isEmpty():
            self._draw_measurements(p)
            self._draw_in_progress(p)
            if self._ruler_mode and self._hover_img:
                self._draw_crosshair(p)

        p.end()

    def _wp(self, ip: QPointF) -> QPointF:
        """Normalised image → widget coords."""
        return self._image_to_widget(ip)

    def _draw_line_with_label(
        self, p: QPainter, a: QPointF, b: QPointF, label: str, color: QColor, alpha: int = 220
    ):
        wa = self._wp(a)
        wb = self._wp(b)

        # End-cap ticks
        line_pen = QPen(color, 1.8, Qt.SolidLine, Qt.RoundCap)
        p.setPen(line_pen)
        p.drawLine(wa, wb)

        # Perpendicular end caps
        dx = wb.x() - wa.x()
        dy = wb.y() - wa.y()
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length * 5, dx / length * 5
        for pt in (wa, wb):
            p.drawLine(QPointF(pt.x() - nx, pt.y() - ny), QPointF(pt.x() + nx, pt.y() + ny))

        # Label background + text
        mid = QPointF((wa.x() + wb.x()) / 2, (wa.y() + wb.y()) / 2)
        font = QFont("JetBrains Mono", 9, QFont.Medium)
        p.setFont(font)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(label) + 10
        th = fm.height() + 4
        bg_rect = QRectF(mid.x() - tw / 2, mid.y() - th / 2, tw, th)

        bg = QColor("#07050F")
        bg.setAlpha(200)
        p.fillRect(bg_rect, bg)
        border_pen = QPen(color, 0.8)
        p.setPen(border_pen)
        p.drawRect(bg_rect)
        p.setPen(color)
        p.drawText(bg_rect, Qt.AlignCenter, label)

    def _draw_measurements(self, p: QPainter):
        colors = [
            QColor("#10B981"),  # emerald
            QColor("#F59E0B"),  # amber
            QColor("#A78BFA"),  # violet
            QColor("#FF6B6B"),  # coral
            QColor("#60A5FA"),  # blue
        ]
        for i, m in enumerate(self._measurements):
            col = colors[i % len(colors)]
            self._draw_line_with_label(p, m.p1, m.p2, m.label, col)

    def _draw_in_progress(self, p: QPainter):
        if not self._drawing or not self._start_img or not self._end_img:
            return
        col = QColor("#FFFFFF")
        col.setAlpha(160)
        pen = QPen(col, 1.5, Qt.DashLine)
        p.setPen(pen)
        p.drawLine(self._wp(self._start_img), self._wp(self._end_img))

        # Live distance hint
        px_d, mm_d = self._px_distance(self._start_img, self._end_img)
        label = f"{mm_d:.1f} mm" if mm_d else f"{px_d:.0f} px"
        wp2 = self._wp(self._end_img)
        p.setPen(QColor("#E2E0FF"))
        p.setFont(QFont("JetBrains Mono", 9))
        p.drawText(QPointF(wp2.x() + 8, wp2.y() - 6), label)

    def _draw_crosshair(self, p: QPainter):
        if not self._hover_img:
            return
        wh = self._wp(self._hover_img)
        pen = QPen(QColor("#7C3AED"), 0.6, Qt.DotLine)
        p.setPen(pen)
        p.drawLine(QPointF(self._img_rect.left(), wh.y()), QPointF(self._img_rect.right(), wh.y()))
        p.drawLine(QPointF(wh.x(), self._img_rect.top()), QPointF(wh.x(), self._img_rect.bottom()))

        # Pixel coords hint
        if self._pixmap:
            ix = int(self._hover_img.x() * self._pixmap.width())
            iy = int(self._hover_img.y() * self._pixmap.height())
            hint = f"({ix}, {iy})"
            p.setPen(QColor("#4A4570"))
            p.setFont(QFont("JetBrains Mono", 8))
            p.drawText(QPointF(wh.x() + 10, wh.y() - 6), hint)
