# Implementation Plan for Claude Code

## Phase 1: Math and data contracts

Create:

- `src/texture_patch/geometry.py`
- `src/texture_patch/reference_grid.py`
- `src/texture_patch/spline_patch.py`
- `src/texture_patch/optimizer.py`

Make these tests pass first:

```bash
python -m pytest tests/test_geometry_contract.py tests/test_spline_contract.py tests/test_optimizer_contract.py
```

Do not start with GUI before these tests pass.

## Phase 2: Minimal GUI

Create:

- `src/texture_patch/app.py`
- `src/texture_patch/views/main_window.py`
- `src/texture_patch/views/panel1_source_view.py`
- `src/texture_patch/views/panel2_texture_view.py`
- `src/texture_patch/views/panel3_patch_view.py`

First goal:

- App starts.
- Layout is correct.
- All three panels render placeholder labels and grids.

## Phase 3: Interactive rectangle

Add panel 1 rectangle manipulation:

- move
- rotate
- scale

Use simple, reliable handles. Make it good enough for manual testing before making it pretty.

## Phase 4: Texture extraction

Implement panel 2 local texture rendering.

Use vector data:

- local line segments
- local intersections
- mapping back to reference world points

## Phase 5: Spline patch and warped texture

Implement panel 3:

- reference grid
- spline control net
- warped texture lines
- residual vectors

## Phase 6: Hill climbing

Add:

- Start/Pause
- Reset
- Step
- iteration count
- accepted count
- current residual value

The optimizer must never accept a worse residual in basic mode.

## Phase 7: Polish and robustness

Add:

- clear colors and line widths
- status messages
- handling of empty texture/intersection data
- reasonable default window size
- robust mouse interaction near panel edges
