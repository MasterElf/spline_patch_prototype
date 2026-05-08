import numpy as np

from texture_patch.geometry import RectTransform
from texture_patch.reference_grid import ReferenceGrid


def test_default_reference_grid_has_expected_line_count():
    grid = ReferenceGrid.create_default(line_count=20, world_size=1000.0)

    assert len(grid.vertical_lines) == 20
    assert len(grid.horizontal_lines) == 20
    assert len(grid.intersections) == 400


def test_extract_texture_has_intersections_with_reference_mapping():
    grid = ReferenceGrid.create_default(line_count=20, world_size=1000.0)
    transform = RectTransform(
        center=np.array([500.0, 500.0]),
        width=300.0,
        height=300.0,
        rotation_radians=0.0,
    )

    texture = grid.extract_texture(transform)

    assert len(texture.line_segments_uv) > 0
    assert len(texture.intersections) > 0

    for intersection in texture.intersections:
        assert 0.0 <= intersection.uv[0] <= 1.0
        assert 0.0 <= intersection.uv[1] <= 1.0
        assert intersection.reference_world_point.shape == (2,)


def test_extract_texture_changes_when_rectangle_rotates():
    grid = ReferenceGrid.create_default(line_count=20, world_size=1000.0)

    unrotated = RectTransform(
        center=np.array([500.0, 500.0]),
        width=300.0,
        height=300.0,
        rotation_radians=0.0,
    )

    rotated = RectTransform(
        center=np.array([500.0, 500.0]),
        width=300.0,
        height=300.0,
        rotation_radians=0.5,
    )

    texture_a = grid.extract_texture(unrotated)
    texture_b = grid.extract_texture(rotated)

    assert len(texture_a.line_segments_uv) > 0
    assert len(texture_b.line_segments_uv) > 0

    first_a = texture_a.line_segments_uv[0]
    first_b = texture_b.line_segments_uv[0]

    assert not np.allclose(first_a.start_uv, first_b.start_uv) or not np.allclose(first_a.end_uv, first_b.end_uv)
