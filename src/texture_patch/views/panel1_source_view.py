"""Panel 1 – source grid and interactive rectangle.

The user can:
  - Drag inside the rectangle to move it.
  - Drag a corner handle to scale both dimensions.
  - Drag an edge-midpoint handle to scale one dimension.
  - Drag the rotation handle (above the top edge) to rotate.

All coordinates are in world space internally.  The widget maintains a
world→widget linear transform that fits the grid into the visible area.
"""

from __future__ import annotations

import math
from enum import Enum, auto

import numpy as np
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QCursor
from PySide6.QtWidgets import QWidget

from texture_patch.geometry import RectTransform
from texture_patch.reference_grid import ReferenceGrid
from texture_patch.settings import GRID, RENDER


# ---------------------------------------------------------------------------
# Handle definitions
# ---------------------------------------------------------------------------


class _HandleKind(Enum):
    NONE = auto()
    MOVE = auto()
    CORNER_TL = auto()
    CORNER_TR = auto()
    CORNER_BR = auto()
    CORNER_BL = auto()
    EDGE_TOP = auto()
    EDGE_RIGHT = auto()
    EDGE_BOTTOM = auto()
    EDGE_LEFT = auto()
    ROTATE = auto()


# (handle_kind, uv_of_handle, uv_of_opposite)  – for scale handles
_SCALE_HANDLES: list[tuple[_HandleKind, np.ndarray, np.ndarray]] = [
    (_HandleKind.CORNER_TL, np.array([0.0, 0.0]), np.array([1.0, 1.0])),
    (_HandleKind.CORNER_TR, np.array([1.0, 0.0]), np.array([0.0, 1.0])),
    (_HandleKind.CORNER_BR, np.array([1.0, 1.0]), np.array([0.0, 0.0])),
    (_HandleKind.CORNER_BL, np.array([0.0, 1.0]), np.array([1.0, 0.0])),
    (_HandleKind.EDGE_TOP,    np.array([0.5, 0.0]), np.array([0.5, 1.0])),
    (_HandleKind.EDGE_RIGHT,  np.array([1.0, 0.5]), np.array([0.0, 0.5])),
    (_HandleKind.EDGE_BOTTOM, np.array([0.5, 1.0]), np.array([0.5, 0.0])),
    (_HandleKind.EDGE_LEFT,   np.array([0.0, 0.5]), np.array([1.0, 0.5])),
]

_MIN_RECT_SIZE = 10.0  # world units


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------


class Panel1SourceView(QWidget):
    """Panel 1: reference grid with an interactive transformed rectangle."""

    rect_transform_changed = Signal(object)  # emits RectTransform

    def __init__(self, grid: ReferenceGrid, rect: RectTransform, parent=None) -> None:
        super().__init__(parent)
        self._grid = grid
        self._rect = rect
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)

        # Drag state
        self._drag_kind = _HandleKind.NONE
        self._drag_start_widget = QPointF()
        self._drag_start_world = np.zeros(2)
        self._drag_start_rect: RectTransform | None = None
        self._drag_initial_angle = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_rect_transform(self, rect: RectTransform) -> None:
        self._rect = rect
        self.update()

    def get_rect_transform(self) -> RectTransform:
        return self._rect

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

    def _world_to_widget(self, wx: float, wy: float) -> QPointF:
        s = self._scale()
        ox, oy = self._offset()
        return QPointF(ox + wx * s, oy + wy * s)

    def _widget_to_world(self, pt: QPointF) -> np.ndarray:
        s = self._scale()
        ox, oy = self._offset()
        return np.array([(pt.x() - ox) / s, (pt.y() - oy) / s])

    def _world_np_to_widget(self, pt: np.ndarray) -> QPointF:
        return self._world_to_widget(float(pt[0]), float(pt[1]))

    # ------------------------------------------------------------------
    # Handle positions and hit-testing
    # ------------------------------------------------------------------

    def _rotation_handle_world(self) -> np.ndarray:
        return self._rect.local_to_world(
            np.array([0.5, RENDER.rotation_handle_v_offset])
        )

    def _hit_handle(self, widget_pt: QPointF) -> _HandleKind:
        r = RENDER.handle_radius + 2  # slightly larger hit radius

        # Rotation handle first (it's outside the rect so check separately)
        rh = self._world_np_to_widget(self._rotation_handle_world())
        if (widget_pt - rh).manhattanLength() < r * 2:
            return _HandleKind.ROTATE

        for kind, uv, _ in _SCALE_HANDLES:
            hw = self._world_np_to_widget(self._rect.local_to_world(uv))
            if (widget_pt - hw).manhattanLength() < r * 2:
                return kind

        # Inside rectangle → move
        world_pt = self._widget_to_world(widget_pt)
        if self._rect.contains_world(world_pt):
            return _HandleKind.MOVE

        return _HandleKind.NONE

    # ------------------------------------------------------------------
    # Mouse events
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        widget_pt = event.position()
        world_pt = self._widget_to_world(widget_pt)
        kind = self._hit_handle(widget_pt)
        if kind == _HandleKind.NONE:
            return

        self._drag_kind = kind
        self._drag_start_widget = widget_pt
        self._drag_start_world = world_pt
        self._drag_start_rect = self._rect.copy()

        if kind == _HandleKind.ROTATE:
            rh = self._rotation_handle_world()
            dx = rh[0] - self._rect.center[0]
            dy = rh[1] - self._rect.center[1]
            self._drag_initial_angle = math.atan2(dy, dx)

    def mouseMoveEvent(self, event) -> None:
        widget_pt = event.position()
        if self._drag_kind == _HandleKind.NONE:
            # Update cursor
            kind = self._hit_handle(widget_pt)
            if kind == _HandleKind.ROTATE:
                self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
            elif kind == _HandleKind.MOVE:
                self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
            elif kind != _HandleKind.NONE:
                self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            return

        world_pt = self._widget_to_world(widget_pt)
        r = self._drag_start_rect

        if self._drag_kind == _HandleKind.MOVE:
            delta = world_pt - self._drag_start_world
            new_center = r.center + delta
            self._rect = RectTransform(new_center, r.width, r.height, r.rotation_radians)

        elif self._drag_kind == _HandleKind.ROTATE:
            cx, cy = r.center[0], r.center[1]
            dx = world_pt[0] - cx
            dy = world_pt[1] - cy
            current_angle = math.atan2(dy, dx)
            delta_angle = current_angle - self._drag_initial_angle
            new_rotation = r.rotation_radians + delta_angle
            self._rect = RectTransform(r.center, r.width, r.height, new_rotation)

        else:
            self._rect = self._apply_scale_drag(r, world_pt)

        self.update()
        self.rect_transform_changed.emit(self._rect)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_kind = _HandleKind.NONE

    def _apply_scale_drag(self, r: RectTransform, mouse_world: np.ndarray) -> RectTransform:
        """Compute new RectTransform when a scale handle is dragged."""
        # Find the opposite UV and its fixed world position
        opp_uv: np.ndarray | None = None
        for kind, uv_h, uv_opp in _SCALE_HANDLES:
            if kind == self._drag_kind:
                opp_uv = uv_opp
                break
        if opp_uv is None:
            return r

        opp_world = r.local_to_world(opp_uv)
        new_center = (opp_world + mouse_world) / 2.0

        # Displacement from new_center to mouse in rotated local frame
        dp = mouse_world - new_center
        c = math.cos(r.rotation_radians)
        s = math.sin(r.rotation_radians)
        dp_lx = dp[0] * c + dp[1] * s
        dp_ly = -dp[0] * s + dp[1] * c

        is_corner = self._drag_kind in (
            _HandleKind.CORNER_TL, _HandleKind.CORNER_TR,
            _HandleKind.CORNER_BR, _HandleKind.CORNER_BL,
        )
        is_horiz = self._drag_kind in (_HandleKind.EDGE_TOP, _HandleKind.EDGE_BOTTOM)
        is_vert = self._drag_kind in (_HandleKind.EDGE_LEFT, _HandleKind.EDGE_RIGHT)

        if is_corner:
            new_width = max(2.0 * abs(dp_lx), _MIN_RECT_SIZE)
            new_height = max(2.0 * abs(dp_ly), _MIN_RECT_SIZE)
        elif is_horiz:
            new_width = r.width
            new_height = max(2.0 * abs(dp_ly), _MIN_RECT_SIZE)
        else:  # is_vert
            new_width = max(2.0 * abs(dp_lx), _MIN_RECT_SIZE)
            new_height = r.height

        return RectTransform(new_center, new_width, new_height, r.rotation_radians)

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(245, 245, 245))

        self._draw_grid(painter)
        self._draw_rectangle(painter)
        self._draw_handles(painter)

    def _draw_grid(self, painter: QPainter) -> None:
        r, g, b = RENDER.grid_line_color
        painter.setPen(QPen(QColor(r, g, b), 1))
        for p0, p1 in self._grid.vertical_lines + self._grid.horizontal_lines:
            painter.drawLine(
                self._world_np_to_widget(p0),
                self._world_np_to_widget(p1),
            )

    def _draw_rectangle(self, painter: QPainter) -> None:
        corners = self._rect.corners_world()
        r, g, b = RENDER.rect_outline_color
        painter.setPen(QPen(QColor(r, g, b), 2))
        n = len(corners)
        for i in range(n):
            painter.drawLine(
                self._world_np_to_widget(corners[i]),
                self._world_np_to_widget(corners[(i + 1) % n]),
            )
        # Draw a dashed line from top-edge center to rotation handle
        rh_world = self._rotation_handle_world()
        top_center = self._rect.local_to_world(np.array([0.5, 0.0]))
        pen = QPen(QColor(r, g, b), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(
            self._world_np_to_widget(top_center),
            self._world_np_to_widget(rh_world),
        )

    def _draw_handles(self, painter: QPainter) -> None:
        rad = RENDER.handle_radius
        fr, fg, fb = RENDER.handle_fill_color
        or_, og, ob = RENDER.handle_outline_color
        fill = QBrush(QColor(fr, fg, fb))
        outline = QPen(QColor(or_, og, ob), 1)

        painter.setPen(outline)
        painter.setBrush(fill)
        for _, uv, _ in _SCALE_HANDLES:
            hw = self._world_np_to_widget(self._rect.local_to_world(uv))
            painter.drawRect(
                int(hw.x() - rad), int(hw.y() - rad), rad * 2, rad * 2
            )

        # Rotation handle
        rr, rg, rb = RENDER.rotation_handle_color
        painter.setPen(QPen(QColor(rr, rg, rb), 1))
        painter.setBrush(QBrush(QColor(rr, rg, rb, 180)))
        rh = self._world_np_to_widget(self._rotation_handle_world())
        painter.drawEllipse(rh, float(rad), float(rad))
