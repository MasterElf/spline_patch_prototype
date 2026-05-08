"""Reference grid and texture extraction.

The ReferenceGrid lives in world coordinates.  extract_texture() clips the
visible portion of that grid to a RectTransform and expresses everything in
normalized (u, v) texture coordinates.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from texture_patch.geometry import RectTransform


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class LineSegment:
    """A line segment expressed in texture (u, v) coordinates."""

    start_uv: np.ndarray
    end_uv: np.ndarray


@dataclass
class TextureIntersection:
    """A single grid-intersection point in texture and world coordinates."""

    uv: np.ndarray
    reference_world_point: np.ndarray


@dataclass
class TextureData:
    """All texture information extracted from a reference grid."""

    line_segments_uv: list[LineSegment] = field(default_factory=list)
    intersections: list[TextureIntersection] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.intersections) == 0


# ---------------------------------------------------------------------------
# Clipping helpers
# ---------------------------------------------------------------------------


def _clip_segment_to_unit_square(
    uv0: np.ndarray, uv1: np.ndarray
) -> tuple[np.ndarray, np.ndarray] | None:
    """Liang-Barsky clip of a segment to [0,1]×[0,1].

    Returns clipped (start, end) or None if entirely outside.
    """
    dx = uv1[0] - uv0[0]
    dy = uv1[1] - uv0[1]

    t0, t1 = 0.0, 1.0

    tests = [
        (-dx, float(uv0[0])),      # left:   u ≥ 0
        (dx, 1.0 - float(uv0[0])), # right:  u ≤ 1
        (-dy, float(uv0[1])),      # top:    v ≥ 0
        (dy, 1.0 - float(uv0[1])), # bottom: v ≤ 1
    ]

    for p, q in tests:
        if p == 0.0:
            if q < 0.0:
                return None
        elif p < 0.0:
            t0 = max(t0, q / p)
        else:
            t1 = min(t1, q / p)

    if t0 > t1:
        return None

    d = uv1 - uv0
    return uv0 + t0 * d, uv0 + t1 * d


# ---------------------------------------------------------------------------
# Reference grid
# ---------------------------------------------------------------------------


class ReferenceGrid:
    """A regular 2-D grid of lines and intersection points in world coordinates.

    Attributes
    ----------
    vertical_lines:
        List of ((x0, y0), (x1, y1)) tuples for each vertical line.
    horizontal_lines:
        List of ((x0, y0), (x1, y1)) tuples for each horizontal line.
    intersections:
        List of (x, y) world-coordinate intersection points.
    """

    def __init__(
        self,
        vertical_lines: list[tuple[np.ndarray, np.ndarray]],
        horizontal_lines: list[tuple[np.ndarray, np.ndarray]],
        intersections: list[np.ndarray],
        world_size: float,
    ) -> None:
        self.vertical_lines = vertical_lines
        self.horizontal_lines = horizontal_lines
        self.intersections = intersections
        self.world_size = world_size

    @classmethod
    def create_default(cls, line_count: int = 20, world_size: float = 1000.0) -> "ReferenceGrid":
        """Create a uniform line_count × line_count grid covering [0, world_size]²."""
        positions = [i * world_size / (line_count - 1) for i in range(line_count)]

        vertical_lines: list[tuple[np.ndarray, np.ndarray]] = [
            (np.array([x, 0.0]), np.array([x, world_size])) for x in positions
        ]
        horizontal_lines: list[tuple[np.ndarray, np.ndarray]] = [
            (np.array([0.0, y]), np.array([world_size, y])) for y in positions
        ]
        intersections: list[np.ndarray] = [
            np.array([x, y]) for x in positions for y in positions
        ]

        return cls(vertical_lines, horizontal_lines, intersections, world_size)

    # ------------------------------------------------------------------
    # Texture extraction
    # ------------------------------------------------------------------

    def extract_texture(self, rect_transform: RectTransform) -> TextureData:
        """Clip the grid to rect_transform and express everything in UV coords."""
        segments: list[LineSegment] = []
        intersections: list[TextureIntersection] = []

        # Clip each grid line into UV space
        all_lines = self.vertical_lines + self.horizontal_lines
        for p0_world, p1_world in all_lines:
            uv0 = rect_transform.world_to_local(p0_world)
            uv1 = rect_transform.world_to_local(p1_world)
            clipped = _clip_segment_to_unit_square(uv0, uv1)
            if clipped is not None:
                segments.append(LineSegment(start_uv=clipped[0], end_uv=clipped[1]))

        # Collect intersections that fall inside the rectangle
        for world_pt in self.intersections:
            uv = rect_transform.world_to_local(world_pt)
            if 0.0 <= uv[0] <= 1.0 and 0.0 <= uv[1] <= 1.0:
                intersections.append(
                    TextureIntersection(
                        uv=uv.copy(),
                        reference_world_point=world_pt.copy(),
                    )
                )

        return TextureData(line_segments_uv=segments, intersections=intersections)
