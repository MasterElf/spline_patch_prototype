"""Bicubic spline patch with a 5×5 control-node grid.

Evaluation strategy
-------------------
1. For each of the 5 rows, interpolate the 5 control points at parameter u
   using Catmull-Rom with endpoint extrapolation.
2. Interpolate the 5 resulting intermediate points at parameter v.

This gives a separable patch whose corners pass exactly through the corner
nodes and whose interior is C1 continuous.

Endpoint extrapolation
----------------------
For the first and last segment we extend the control polygon:
    p[-1] = 2*p[0] - p[1]
    p[N]  = 2*p[N-1] - p[N-2]
This makes Catmull-Rom reproduce linear data exactly, which the test suite
relies on.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


class SplinePatch:
    """5×5 bicubic Catmull-Rom patch mapping (u, v) ∈ [0,1]² → ℝ²."""

    _SHAPE = (5, 5, 2)

    def __init__(self, nodes: ArrayLike) -> None:
        nodes = np.asarray(nodes, dtype=float)
        if nodes.shape != self._SHAPE:
            raise ValueError(
                f"nodes must have shape {self._SHAPE}, got {nodes.shape}"
            )
        self._nodes = nodes.copy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, uv: ArrayLike) -> np.ndarray:
        """Evaluate the patch at a single (u, v) ∈ [0, 1]²."""
        uv = np.asarray(uv, dtype=float)
        u, v = float(uv[0]), float(uv[1])

        # Interpolate each row at u → 5 intermediate points
        row_points = np.array([
            self._catmull_rom_1d(self._nodes[row, :, :], u)
            for row in range(5)
        ])

        # Interpolate the 5 intermediate points at v
        return self._catmull_rom_1d(row_points, v)

    def evaluate_many(self, uvs: np.ndarray) -> np.ndarray:
        """Evaluate the patch at each row of *uvs*, shape (N, 2) → (N, 2)."""
        return np.array([self.evaluate(uv) for uv in uvs])

    def copy_nodes(self) -> np.ndarray:
        """Return a copy of the internal (5, 5, 2) node array."""
        return self._nodes.copy()

    def set_nodes(self, nodes: ArrayLike) -> None:
        """Replace the internal node array (must be shaped (5, 5, 2))."""
        nodes = np.asarray(nodes, dtype=float)
        if nodes.shape != self._SHAPE:
            raise ValueError(
                f"nodes must have shape {self._SHAPE}, got {nodes.shape}"
            )
        self._nodes = nodes.copy()

    @classmethod
    def create_default(cls, world_rect=None) -> "SplinePatch":
        """Create an initial patch.

        If *world_rect* is a RectTransform the patch spans its bounding box.
        Otherwise a unit [0, 100]² patch is returned (useful for isolated tests).
        """
        nodes = np.zeros(cls._SHAPE, dtype=float)

        if world_rect is not None:
            min_x, min_y, max_x, max_y = world_rect.bounding_box_world()
            # Add a small padding so the initial residual is non-zero
            cx = (min_x + max_x) / 2.0
            cy = (min_y + max_y) / 2.0
            half_w = (max_x - min_x) / 2.0 * 1.5
            half_h = (max_y - min_y) / 2.0 * 1.5
            for row in range(5):
                for col in range(5):
                    nodes[row, col, 0] = cx - half_w + col * half_w / 2.0
                    nodes[row, col, 1] = cy - half_h + row * half_h / 2.0
        else:
            for row in range(5):
                for col in range(5):
                    nodes[row, col, 0] = col * 25.0
                    nodes[row, col, 1] = row * 25.0

        return cls(nodes)

    # ------------------------------------------------------------------
    # Internal spline evaluation
    # ------------------------------------------------------------------

    @staticmethod
    def _catmull_rom_1d(points: np.ndarray, t_normalized: float) -> np.ndarray:
        """Catmull-Rom interpolation through *points* at normalised parameter t ∈ [0, 1].

        *points* has shape (N, D).  The parameter is rescaled to [0, N-1].
        Endpoint extrapolation is used for the boundary segments.
        """
        n = len(points)
        t = t_normalized * (n - 1)

        # Clamp to the last valid segment
        i = int(min(t, n - 2))
        local_t = t - i

        def get(idx: int) -> np.ndarray:
            if idx < 0:
                return 2.0 * points[0] - points[1]
            if idx >= n:
                return 2.0 * points[n - 1] - points[n - 2]
            return points[idx]

        p0 = get(i - 1)
        p1 = get(i)
        p2 = get(i + 1)
        p3 = get(i + 2)

        t2 = local_t * local_t
        t3 = t2 * local_t

        return 0.5 * (
            2.0 * p1
            + (-p0 + p2) * local_t
            + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
            + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
        )
