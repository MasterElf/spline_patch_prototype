"""Residual calculation and hill-climb optimizer.

The optimizer perturbs all 25 spline control nodes by Gaussian noise scaled
by step_size.  A perturbation is accepted only if it strictly improves the
total sum-of-squares residual (basic hill climb; never accepts a worse step).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from texture_patch.reference_grid import TextureData
from texture_patch.spline_patch import SplinePatch


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class Residual:
    """Residual information for a single texture intersection."""

    uv: np.ndarray
    warped_point: np.ndarray
    target_point: np.ndarray
    vector: np.ndarray  # target_point - warped_point


@dataclass
class OptimizationStepResult:
    """Result returned by HillClimbOptimizer.step()."""

    iteration: int
    accepted: bool
    best_score: float


# ---------------------------------------------------------------------------
# Residual calculator (stateless, static methods)
# ---------------------------------------------------------------------------


class ResidualCalculator:
    """Computes residuals between texture intersections and spline warped points."""

    @staticmethod
    def compute_residuals(patch: SplinePatch, texture: TextureData) -> list[Residual]:
        """Return one Residual per texture intersection."""
        results: list[Residual] = []
        for intersection in texture.intersections:
            warped = patch.evaluate(intersection.uv)
            target = intersection.reference_world_point
            vector = target - warped
            results.append(
                Residual(
                    uv=intersection.uv.copy(),
                    warped_point=warped,
                    target_point=target.copy(),
                    vector=vector,
                )
            )
        return results

    @staticmethod
    def compute_total_residual(patch: SplinePatch, texture: TextureData) -> float:
        """Return the sum of squared residual lengths."""
        total = 0.0
        for intersection in texture.intersections:
            warped = patch.evaluate(intersection.uv)
            diff = intersection.reference_world_point - warped
            total += float(np.dot(diff, diff))
        return total


# ---------------------------------------------------------------------------
# Hill-climb optimizer
# ---------------------------------------------------------------------------


class HillClimbOptimizer:
    """Basic hill-climb optimizer for SplinePatch control nodes.

    Rules
    -----
    - Each step randomly perturbs *all* 25 nodes by Gaussian noise.
    - Accept only if the new total residual is strictly better (lower).
    - Never accept a worse state.
    """

    def __init__(
        self,
        patch: SplinePatch,
        texture: TextureData,
        random_seed: int | None = None,
        step_size: float = 5.0,
    ) -> None:
        self._patch = patch
        self._texture = texture
        self._step_size = step_size
        self._rng = np.random.default_rng(random_seed)

        self._best_nodes = patch.copy_nodes()
        self._best_score = ResidualCalculator.compute_total_residual(patch, texture)
        self._iteration = 0
        self._accepted_count = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def best_score(self) -> float:
        return self._best_score

    @property
    def iteration(self) -> int:
        return self._iteration

    @property
    def accepted_count(self) -> int:
        return self._accepted_count

    @property
    def step_size(self) -> float:
        return self._step_size

    @step_size.setter
    def step_size(self, value: float) -> None:
        self._step_size = max(float(value), 1e-6)

    # ------------------------------------------------------------------
    # Core step
    # ------------------------------------------------------------------

    def step(self) -> OptimizationStepResult:
        """Run one hill-climb iteration.

        Returns an OptimizationStepResult with iteration count, whether the
        step was accepted, and the current best score.
        """
        self._iteration += 1

        perturbation = self._rng.normal(0.0, self._step_size, self._best_nodes.shape)
        candidate_nodes = self._best_nodes + perturbation

        self._patch.set_nodes(candidate_nodes)
        new_score = ResidualCalculator.compute_total_residual(self._patch, self._texture)

        if new_score < self._best_score:
            self._best_nodes = candidate_nodes
            self._best_score = new_score
            accepted = True
            self._accepted_count += 1
        else:
            # Reject: restore best nodes
            self._patch.set_nodes(self._best_nodes)
            accepted = False

        return OptimizationStepResult(
            iteration=self._iteration,
            accepted=accepted,
            best_score=self._best_score,
        )

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self, patch: SplinePatch, texture: TextureData) -> None:
        """Reinitialise the optimizer with a new patch and texture."""
        self._patch = patch
        self._texture = texture
        self._best_nodes = patch.copy_nodes()
        self._best_score = ResidualCalculator.compute_total_residual(patch, texture)
        self._iteration = 0
        self._accepted_count = 0
