import math

import numpy as np
import pytest

from texture_patch.geometry import RectTransform


def assert_close(actual, expected, tolerance=1e-6):
    assert np.allclose(np.asarray(actual), np.asarray(expected), atol=tolerance), f"{actual} != {expected}"


def test_rect_transform_round_trips_local_coordinates():
    transform = RectTransform(
        center=np.array([100.0, 50.0]),
        width=40.0,
        height=20.0,
        rotation_radians=math.radians(30.0),
    )

    samples = [
        np.array([0.0, 0.0]),
        np.array([1.0, 0.0]),
        np.array([0.0, 1.0]),
        np.array([1.0, 1.0]),
        np.array([0.5, 0.5]),
        np.array([0.25, 0.75]),
    ]

    for uv in samples:
        world = transform.local_to_world(uv)
        round_tripped = transform.world_to_local(world)
        assert_close(round_tripped, uv)


def test_rect_transform_center_maps_to_local_half_half():
    transform = RectTransform(
        center=np.array([12.0, 34.0]),
        width=80.0,
        height=60.0,
        rotation_radians=math.radians(-15.0),
    )

    assert_close(transform.world_to_local(np.array([12.0, 34.0])), np.array([0.5, 0.5]))


def test_rect_transform_contains_world_point():
    transform = RectTransform(
        center=np.array([0.0, 0.0]),
        width=10.0,
        height=20.0,
        rotation_radians=0.0,
    )

    assert transform.contains_world(np.array([0.0, 0.0]))
    assert transform.contains_world(np.array([4.9, 9.9]))
    assert not transform.contains_world(np.array([5.1, 0.0]))
    assert not transform.contains_world(np.array([0.0, 10.1]))


def test_rect_transform_rejects_invalid_size():
    with pytest.raises(ValueError):
        RectTransform(
            center=np.array([0.0, 0.0]),
            width=0.0,
            height=10.0,
            rotation_radians=0.0,
        )

    with pytest.raises(ValueError):
        RectTransform(
            center=np.array([0.0, 0.0]),
            width=10.0,
            height=-1.0,
            rotation_radians=0.0,
        )
