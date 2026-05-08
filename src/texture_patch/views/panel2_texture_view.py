"""Panel 2 – local texture view.

Shows the content visible through the rectangle in panel 1 expressed in
normalized (u, v) coordinates.  The rectangle is always axis-aligned here;
grid lines appear rotated relative to the panel if the source rectangle is
rotated.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget

from texture_patch.reference_grid import TextureData
from texture_patch.settings import RENDER


class Panel2TextureView(QWidget):
    """Panel 2: displays the extracted texture in normalized UV space."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._texture: TextureData = TextureData()
        self.setMinimumSize(150, 150)

    def set_texture_data(self, texture: TextureData) -> None:
        self._texture = texture
        self.update()

    # ------------------------------------------------------------------
    # UV ↔ widget transform
    # ------------------------------------------------------------------

    def _uv_to_widget(self, uv: np.ndarray) -> QPointF:
        m = RENDER.margin_pixels
        w = self.width() - 2 * m
        h = self.height() - 2 * m
        # Keep square aspect ratio
        side = min(w, h)
        ox = m + (w - side) / 2.0
        oy = m + (h - side) / 2.0
        return QPointF(ox + float(uv[0]) * side, oy + float(uv[1]) * side)

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(250, 250, 250))

        self._draw_rect_border(painter)

        if self._texture.is_empty():
            self._draw_empty_label(painter)
            return

        self._draw_line_segments(painter)
        self._draw_intersections(painter)

    def _draw_rect_border(self, painter: QPainter) -> None:
        """Draw the UV [0,1]² rectangle boundary."""
        tl = self._uv_to_widget(np.array([0.0, 0.0]))
        br = self._uv_to_widget(np.array([1.0, 1.0]))
        painter.setPen(QPen(QColor(100, 100, 220), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawRect(
            int(tl.x()), int(tl.y()),
            int(br.x() - tl.x()), int(br.y() - tl.y()),
        )

    def _draw_line_segments(self, painter: QPainter) -> None:
        r, g, b = RENDER.texture_line_color
        painter.setPen(QPen(QColor(r, g, b), 1))
        for seg in self._texture.line_segments_uv:
            painter.drawLine(
                self._uv_to_widget(seg.start_uv),
                self._uv_to_widget(seg.end_uv),
            )

    def _draw_intersections(self, painter: QPainter) -> None:
        r, g, b = RENDER.texture_intersection_color
        painter.setPen(QPen(QColor(r, g, b), 1))
        painter.setBrush(QBrush(QColor(r, g, b)))
        for intr in self._texture.intersections:
            pt = self._uv_to_widget(intr.uv)
            painter.drawEllipse(pt, 2.5, 2.5)

    def _draw_empty_label(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor(150, 150, 150)))
        painter.drawText(self.rect(), "No visible intersections")
