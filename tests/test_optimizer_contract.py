import numpy as np

from texture_patch.optimizer import HillClimbOptimizer, ResidualCalculator
from texture_patch.reference_grid import TextureData, TextureIntersection
from texture_patch.spline_patch import SplinePatch


def create_identity_nodes():
    nodes = np.zeros((5, 5, 2), dtype=float)

    for row in range(5):
        for column in range(5):
            nodes[row, column, 0] = column * 25.0
            nodes[row, column, 1] = row * 25.0

    return nodes


def create_simple_texture_data():
    intersections = [
        TextureIntersection(uv=np.array([0.0, 0.0]), reference_world_point=np.array([0.0, 0.0])),
        TextureIntersection(uv=np.array([0.5, 0.5]), reference_world_point=np.array([50.0, 50.0])),
        TextureIntersection(uv=np.array([1.0, 1.0]), reference_world_point=np.array([100.0, 100.0])),
    ]

    return TextureData(line_segments_uv=[], intersections=intersections)


def test_residual_is_zero_for_identity_patch_and_matching_texture_data():
    patch = SplinePatch(create_identity_nodes())
    texture = create_simple_texture_data()

    total = ResidualCalculator.compute_total_residual(patch, texture)

    assert total == 0.0


def test_optimizer_never_worsens_best_score():
    nodes = create_identity_nodes()
    nodes[:, :, 0] += 10.0

    patch = SplinePatch(nodes)
    texture = create_simple_texture_data()

    optimizer = HillClimbOptimizer(
        patch=patch,
        texture=texture,
        random_seed=123,
        step_size=1.0,
    )

    initial_score = optimizer.best_score

    for _ in range(100):
        optimizer.step()

    assert optimizer.best_score <= initial_score


def test_optimizer_result_reports_iteration_and_acceptance():
    nodes = create_identity_nodes()
    nodes[:, :, 0] += 10.0

    patch = SplinePatch(nodes)
    texture = create_simple_texture_data()

    optimizer = HillClimbOptimizer(
        patch=patch,
        texture=texture,
        random_seed=123,
        step_size=1.0,
    )

    result = optimizer.step()

    assert result.iteration == 1
    assert isinstance(result.accepted, bool)
    assert result.best_score == optimizer.best_score
