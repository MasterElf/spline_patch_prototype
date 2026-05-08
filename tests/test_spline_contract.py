import numpy as np

from texture_patch.spline_patch import SplinePatch


def assert_close(actual, expected, tolerance=1e-5):
    assert np.allclose(np.asarray(actual), np.asarray(expected), atol=tolerance), f"{actual} != {expected}"


def create_identity_nodes():
    nodes = np.zeros((5, 5, 2), dtype=float)

    for row in range(5):
        for column in range(5):
            nodes[row, column, 0] = column * 25.0
            nodes[row, column, 1] = row * 25.0

    return nodes


def test_spline_patch_evaluates_corners():
    patch = SplinePatch(create_identity_nodes())

    assert_close(patch.evaluate(np.array([0.0, 0.0])), np.array([0.0, 0.0]))
    assert_close(patch.evaluate(np.array([1.0, 0.0])), np.array([100.0, 0.0]))
    assert_close(patch.evaluate(np.array([0.0, 1.0])), np.array([0.0, 100.0]))
    assert_close(patch.evaluate(np.array([1.0, 1.0])), np.array([100.0, 100.0]))


def test_spline_patch_identity_grid_is_linear():
    patch = SplinePatch(create_identity_nodes())

    assert_close(patch.evaluate(np.array([0.5, 0.5])), np.array([50.0, 50.0]))
    assert_close(patch.evaluate(np.array([0.25, 0.75])), np.array([25.0, 75.0]))
    assert_close(patch.evaluate(np.array([0.8, 0.2])), np.array([80.0, 20.0]))


def test_spline_patch_evaluate_many_matches_single_evaluation():
    patch = SplinePatch(create_identity_nodes())
    uvs = np.array(
        [
            [0.0, 0.0],
            [0.5, 0.5],
            [1.0, 1.0],
            [0.25, 0.75],
        ],
        dtype=float,
    )

    many = patch.evaluate_many(uvs)

    assert many.shape == (4, 2)

    for index, uv in enumerate(uvs):
        assert_close(many[index], patch.evaluate(uv))


def test_spline_patch_rejects_wrong_node_shape():
    wrong_shape = np.zeros((4, 5, 2), dtype=float)

    try:
        SplinePatch(wrong_shape)
    except ValueError:
        return

    raise AssertionError("SplinePatch must reject node arrays that are not shaped (5, 5, 2).")
