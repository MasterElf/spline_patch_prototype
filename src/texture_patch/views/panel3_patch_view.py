"""Panel 3 – spline patch, warped texture, and residual vectors.

Shows:
  - The same reference grid as panel 1.
  - The 5×5 spline control net.
  - The texture from panel 2 mapped through the spline patch.
  - Residual vectors from each warped intersection to its target.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget

from texture_patch.optimizer import Residual, ResidualCalculator
from texture_patch.reference_grid import ReferenceGrid, TextureData
from texture_patch.settings import GRID, RENDER
from texture_patch.spline_patch import SplinePatch


class Panel3PatchView(QWidget):
    """Panel 3: target grid, spline patch, warped texture, residuals."""

    def __init__(self, grid: ReferenceGrid, patch: SplinePatch, parent=None) -> None:
        super().__init__(parent)
        self._grid = grid
        self._patch = patch
        self._texture: TextureData = TextureData()
        self._residuals: list[Residual] = []
        self.setMinimumSize(200, 300)

    def set_patch(self, patch: SplinePatch) -> None:
        self._patch = patch
        self._refresh_residuals()
        self.update()

    def set_texture_data(self, texture: TextureData) -> None:
        self._texture = texture
        self._refresh_residuals()
        self.update()

    def refresh(self) -> None:
        """Recompute residuals from current patch and texture, then repaint."""
        self._refresh_residuals()
        self.update()

    def _refresh_residuals(self) -> None:
        if not self._texture.is_empty():
            self._residuals = ResidualCalculator.compute_residuals(self._patch, self._texture)
        else:
            self._residuals = []

    # ------------------------------------------------------------------
    # World ↔ widget transform
    # ------------------------------------------------------------------

    def _scale(self) -> float:
        m = RENDER.margin_pixels
        w = self.width() - 2 * m
        h = self.height() - 2 * m
        return min(w, h) / self._grid.world_size

    def _offset(self) -> tuple[float, float]:
        m = RENDER.margin_pixels
        s = self._scale()
        ox = m + (self.width() - 2 * m - s * self._grid.world_size) / 2.0
        oy = m + (self.height() - 2 * m - s * self._grid.world_size) / 2.0
        return ox, oy

    def _world_to_widget(self, pt: np.ndarray) -> QPointF:
        s = self._scale()
        ox, oy = self._offset()
        return QPointF(ox + float(pt[0]) * s, oy + float(pt[1]) * s)

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(245, 245, 245))

        self._draw_grid(painter)
        self._draw_warped_texture(painter)
        self._draw_patch_net(painter)
        self._draw_residuals(painter)

    # ------------------------------------------------------------------
    # Grid
    # ------------------------------------------------------------------

    def _draw_grid(self, painter: QPainter) -> None:
        r, g, b = RENDER.grid_line_color
        painter.setPen(QPen(QColor(r, g, b), 1))
        for p0, p1 in self._grid.vertical_lines + self._grid.horizontal_lines:
            painter.drawLine(self._world_to_widget(p0), self._world_to_widget(p1))

    # ------------------------------------------------------------------
    # Warped texture
    # ------------------------------------------------------------------

    def _draw_warped_texture(self, painter: QPainter) -> None:
        if self._texture.is_empty():
            return
        r, g, b = RENDER.warped_texture_color
        painter.setPen(QPen(QColor(r, g, b), 1))
        n = RENDER.texture_samples_per_segment
        for seg in self._texture.line_segments_uv:
            pts = [
                self._world_to_widget(
                    self._patch.evaluate(
                        seg.start_uv + (seg.end_uv - seg.start_uv) * (i / (n - 1))
                    )
                )
                for i in range(n)
            ]
            for i in range(len(pts) - 1):
                painter.drawLine(pts[i], pts[i + 1])

    # ------------------------------------------------------------------
    # Spline control net
    # ------------------------------------------------------------------

    def _draw_patch_net(self, painter: QPainter) -> None:
        nodes = self._patch.copy_nodes()
        nr, ng, nb = RENDER.patch_net_color
        pn_r, pn_g, pn_b = RENDER.patch_node_color
        net_pen = QPen(QColor(nr, ng, nb), 1)
        node_pen = QPen(QColor(pn_r, pn_g, pn_b), 1)
        node_brush = QBrush(QColor(pn_r, pn_g, pn_b, 200))

        painter.setPen(net_pen)
        # Horizontal connections
        for row in range(5):
            for col in range(4):
                p0 = self._world_to_widget(nodes[row, col])
                p1 = self._world_to_widget(nodes[row, col + 1])
                painter.drawLine(p0, p1)
        # Vertical connections
        for col in range(5):
            for row in range(4):
                p0 = self._world_to_widget(nodes[row, col])
                p1 = self._world_to_widget(nodes[row + 1, col])
                painter.drawLine(p0, p1)

        # Node dots
        painter.setPen(node_pen)
        painter.setBrush(node_brush)
        for row in range(5):
            for col in range(5):
                pt = self._world_to_widget(nodes[row, col])
                painter.drawEllipse(pt, 3.5, 3.5)

    # ------------------------------------------------------------------
    # Residual vectors
    # ------------------------------------------------------------------

    def _draw_residuals(self, painter: QPainter) -> None:
        if not self._residuals:
            return
        r, g, b = RENDER.residual_color
        painter.setPen(QPen(QColor(r, g, b), 1))
        painter.setBrush(QBrush(QColor(r, g, b)))
        for res in self._residuals:
            wp = self._world_to_widget(res.warped_point)
            tp = self._world_to_widget(res.target_point)
            painter.drawLine(wp, tp)
            # Small circle at the warped point
            painter.drawEllipse(wp, 2.0, 2.0)
