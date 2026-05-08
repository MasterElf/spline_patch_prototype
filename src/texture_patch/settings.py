"""Application-wide configuration constants collected in dataclasses."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GridSettings:
    line_count: int = 20
    world_size: float = 1000.0

    @property
    def spacing(self) -> float:
        return self.world_size / (self.line_count - 1)


@dataclass(frozen=True)
class OptimizationSettings:
    step_size: float = 5.0
    steps_per_tick: int = 5
    timer_interval_ms: int = 30
    min_step_size: float = 0.1
    # Adaptive step: effective_step = min(step_size, max_residual * residual_step_fraction)
    residual_step_fraction: float = 0.10


@dataclass(frozen=True)
class RenderSettings:
    margin_pixels: int = 20
    handle_radius: int = 7
    rotation_handle_v_offset: float = -0.18
    texture_samples_per_segment: int = 16

    # Colors as (R, G, B)
    grid_line_color: tuple[int, int, int] = (180, 180, 180)
    rect_outline_color: tuple[int, int, int] = (30, 100, 220)
    handle_fill_color: tuple[int, int, int] = (255, 140, 0)
    handle_outline_color: tuple[int, int, int] = (180, 90, 0)
    rotation_handle_color: tuple[int, int, int] = (200, 50, 200)
    texture_line_color: tuple[int, int, int] = (0, 160, 60)
    texture_intersection_color: tuple[int, int, int] = (0, 100, 30)
    residual_color: tuple[int, int, int] = (210, 30, 30)
    patch_node_color: tuple[int, int, int] = (80, 80, 220)
    patch_net_color: tuple[int, int, int] = (160, 160, 240)
    warped_texture_color: tuple[int, int, int] = (0, 180, 80)


# Shared singletons used throughout the app
GRID = GridSettings()
OPT = OptimizationSettings()
RENDER = RenderSettings()
