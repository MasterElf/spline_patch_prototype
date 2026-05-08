import math

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


# ---------------------------------------------------------------------------
# Adaptive step-size tests
# ---------------------------------------------------------------------------


def test_compute_max_residual_length_returns_largest():
    # Identity nodes map uv to [0, 100].
    # Target points are deliberately mismatched: distances 10, 30, 50.
    patch = SplinePatch(create_identity_nodes())
    intersections = [
        TextureIntersection(uv=np.array([0.0, 0.0]), reference_world_point=np.array([10.0, 0.0])),
        TextureIntersection(uv=np.array([0.5, 0.0]), reference_world_point=np.array([50.0 + 30.0, 0.0])),
        TextureIntersection(uv=np.array([0.0, 0.5]), reference_world_point=np.array([0.0, 50.0 + 50.0])),
    ]
    texture = TextureData(line_segments_uv=[], intersections=intersections)

    max_len = ResidualCalculator.compute_max_residual_length(patch, texture)

    assert math.isclose(max_len, 50.0, rel_tol=1e-6)


def test_compute_max_residual_length_is_zero_for_empty_texture():
    patch = SplinePatch(create_identity_nodes())
    texture = TextureData(line_segments_uv=[], intersections=[])

    assert ResidualCalculator.compute_max_residual_length(patch, texture) == 0.0


def test_effective_step_never_exceeds_configured_step_size():
    configured_step = 2.0
    nodes = create_identity_nodes()
    nodes[:, :, 0] += 20.0  # offset so residuals exist

    patch = SplinePatch(nodes)
    texture = create_simple_texture_data()

    optimizer = HillClimbOptimizer(
        patch=patch,
        texture=texture,
        random_seed=0,
        step_size=configured_step,
    )

    for _ in range(50):
        result = optimizer.step()
        assert result.effective_step_size <= configured_step + 1e-12


def test_effective_step_is_smaller_when_residuals_are_small():
    configured_step = 100.0
    # Build a patch that is very close to the target (small residuals).
    nodes = create_identity_nodes()
    nodes[:, :, 0] += 0.5  # tiny offset → tiny residuals
    patch = SplinePatch(nodes)
    texture = create_simple_texture_data()

    optimizer = HillClimbOptimizer(
        patch=patch,
        texture=texture,
        random_seed=0,
        step_size=configured_step,
        residual_step_fraction=0.10,
    )

    result = optimizer.step()

    # max_residual ≈ 0.5, so effective_step ≈ 0.05  ≪  configured_step=100
    assert result.effective_step_size < configured_step


def test_effective_step_is_zero_when_all_residuals_are_zero():
    patch = SplinePatch(create_identity_nodes())
    texture = create_simple_texture_data()  # already matches identity patch

    optimizer = HillClimbOptimizer(
        patch=patch,
        texture=texture,
        random_seed=0,
        step_size=10.0,
    )

    result = optimizer.step()

    assert result.effective_step_size == 0.0
