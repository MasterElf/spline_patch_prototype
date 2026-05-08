"""Geometric primitives for the texture-patch prototype.

The central class is RectTransform, which represents a rectangle in world
space that can be moved, rotated, and scaled.  Normalized local coordinates
(u, v) ∈ [0, 1] × [0, 1] are the texture coordinate system.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike


class RectTransform:
    """Axis-aligned rectangle transformed by translation, rotation, and scale.

    Local (texture) coordinates
    ---------------------------
    u = 0  left edge,   u = 1  right edge
    v = 0  top edge,    v = 1  bottom edge

    World coordinates
    -----------------
    Arbitrary 2-D coordinate system shared with panels 1 and 3.
    """

    def __init__(
        self,
        center: ArrayLike,
        width: float,
        height: float,
        rotation_radians: float,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError(
                f"width and height must be positive, got width={width}, height={height}"
            )
        self.center = np.asarray(center, dtype=float)
        self.width = float(width)
        self.height = float(height)
        self.rotation_radians = float(rotation_radians)

    # ------------------------------------------------------------------
    # Core coordinate transforms
    # ------------------------------------------------------------------

    def local_to_world(self, uv: ArrayLike) -> np.ndarray:
        """Map normalized local (u, v) to world (x, y)."""
        uv = np.asarray(uv, dtype=float)
        lx = (uv[0] - 0.5) * self.width
        ly = (uv[1] - 0.5) * self.height
        c = math.cos(self.rotation_radians)
        s = math.sin(self.rotation_radians)
        wx = self.center[0] + lx * c - ly * s
        wy = self.center[1] + lx * s + ly * c
        return np.array([wx, wy])

    def world_to_local(self, point: ArrayLike) -> np.ndarray:
        """Map world (x, y) to normalized local (u, v).

        Round-trips with local_to_world to floating-point precision.
        """
        point = np.asarray(point, dtype=float)
        dx = point[0] - self.center[0]
        dy = point[1] - self.center[1]
        c = math.cos(self.rotation_radians)
        s = math.sin(self.rotation_radians)
        lx = dx * c + dy * s
        ly = -dx * s + dy * c
        u = lx / self.width + 0.5
        v = ly / self.height + 0.5
        return np.array([u, v])

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def corners_world(self) -> np.ndarray:
        """Return the four world-space corners in order TL, TR, BR, BL."""
        return np.array([
            self.local_to_world(np.array([0.0, 0.0])),
            self.local_to_world(np.array([1.0, 0.0])),
            self.local_to_world(np.array([1.0, 1.0])),
            self.local_to_world(np.array([0.0, 1.0])),
        ])

    def contains_world(self, point: ArrayLike) -> bool:
        """Return True if the world point lies inside (or on the edge of) the rectangle."""
        uv = self.world_to_local(point)
        return bool(0.0 <= uv[0] <= 1.0 and 0.0 <= uv[1] <= 1.0)

    def bounding_box_world(self) -> tuple[float, float, float, float]:
        """Return (min_x, min_y, max_x, max_y) of the world-space bounding box."""
        corners = self.corners_world()
        return (
            float(corners[:, 0].min()),
            float(corners[:, 1].min()),
            float(corners[:, 0].max()),
            float(corners[:, 1].max()),
        )

    def copy(self) -> "RectTransform":
        return RectTransform(
            center=self.center.copy(),
            width=self.width,
            height=self.height,
            rotation_radians=self.rotation_radians,
        )

    def __repr__(self) -> str:
        return (
            f"RectTransform(center={self.center}, width={self.width}, "
            f"height={self.height}, rotation={math.degrees(self.rotation_radians):.1f}°)"
        )
