# Claude Code Project Instructions

## Project goal

Build a Python prototype that demonstrates how a transformed rectangular image region can be extracted, displayed in normalized local coordinates, mapped onto a spline patch, and optimized by hill climbing so the warped texture aligns with a reference grid.

The app has three visual panels arranged like this:

```text
1 | 3
2 | 3
```

Panel 3 spans both rows and is therefore tall/elongated.

## Technology choices

Use:

- Python 3.11+
- PySide6 for the GUI
- NumPy for math
- pytest for non-GUI tests

Avoid OpenCV unless it is clearly necessary. This prototype can render the reference grid and warped texture as vector line segments rather than raster images.

## Core user experience

Panel 1:

- Shows a reference grid with 20 vertical and 20 horizontal grid lines.
- Shows a rectangle on top of the grid.
- The rectangle can be moved, rotated, and scaled with intuitive mouse controls:
  - drag inside rectangle: move
  - drag corner/edge handles: scale
  - drag rotation handle: rotate
- Any transform change immediately updates panels 2 and 3.

Panel 2:

- Shows the content visible through the transformed rectangle from panel 1.
- The rectangle is drawn aligned to panel 2 coordinates.
- The reference grid visible through the rectangle is transformed into the rectangle's local coordinate space.
- If the rectangle is rotated in panel 1, the grid lines should appear rotated in the opposite way inside panel 2.
- Treat this as the "texture" that will be mapped onto the spline patch in panel 3.

Panel 3:

- Shows the same reference grid as panel 1.
- Shows a 5 x 5 control-node spline patch.
- Maps the panel 2 texture onto the spline patch.
- Draws residual vectors between corresponding grid intersections in:
  - the fixed reference grid in panel 3
  - the warped texture mapped onto the spline patch
- Runs a hill-climb optimizer that randomly perturbs all spline control nodes each iteration.
- If the total residual improves, keep the new spline-node positions.
- If the total residual worsens, reject the perturbation and try again.
- The patch should visibly "shake" toward lower residual as optimization runs.

## Important mathematical model

Use normalized texture coordinates:

- `u` in `[0, 1]` from left to right.
- `v` in `[0, 1]` from top to bottom.

Panel 1 rectangle transform:

- Rectangle local coordinates are normalized `(u, v)`.
- `local_to_world((u, v))` maps local rectangle coordinates to panel/grid coordinates.
- `world_to_local((x, y))` maps panel/grid coordinates back to rectangle local coordinates.
- Round-tripping must be numerically stable.

Texture extraction:

- The texture is not a bitmap at first. Represent it as transformed grid line segments and grid intersections in local rectangle coordinates.
- For each reference grid line/intersection in panel 1 that intersects the transformed rectangle, convert it with `world_to_local`.
- Render those local line segments/intersections in panel 2.

Spline patch:

- Use a 5 x 5 array of control nodes.
- The patch evaluates a point `P(u, v)` by first interpolating horizontally and then vertically.
- Interior segments use Catmull-Rom interpolation.
- Outer boundary segments use a simpler Hermite-style spline that matches the derivative at the node where it meets the Catmull-Rom interior spline.
- Keep the implementation isolated and tested.
- It is acceptable to start with a robust Catmull-Rom implementation with safe endpoint extrapolation, then refine the boundary behavior.

Residuals:

- For every texture grid intersection that has a known corresponding reference-grid intersection:
  - Compute where the texture intersection lands on the spline patch: `P(u, v)`.
  - Compare that point to the corresponding reference grid point in panel 3.
  - Residual vector = `target_reference_point - warped_texture_point`.
- Total residual = sum of squared residual lengths.
- Draw residual vectors as small line segments or arrows in panel 3.

## Coding conventions

- Use clear names and small classes.
- Prefer early returns.
- Keep comments in English.
- Use type hints.
- Avoid hard-coded magic numbers by collecting them in settings/dataclasses.
- Keep GUI logic separate from math/optimization logic.
- Do not compare booleans explicitly with `True` or `False`.

## Expected package layout

Create this layout:

```text
src/
  texture_patch/
    __init__.py
    app.py
    settings.py
    geometry.py
    reference_grid.py
    spline_patch.py
    optimizer.py
    views/
      __init__.py
      main_window.py
      panel1_source_view.py
      panel2_texture_view.py
      panel3_patch_view.py
```

The exact layout may evolve, but keep public math modules stable enough for tests.

## Commands

Install:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements-dev.txt
```

Run tests:

```bash
python -m pytest
```

Run the app:

```bash
python -m texture_patch.app
```

On Windows PowerShell, the activation command is:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Implementation strategy

Work in small increments:

1. Create package skeleton and pure math classes.
2. Make tests pass for geometry, reference grid, spline evaluation, and optimizer monotonicity.
3. Build the three-panel PySide6 GUI.
4. Add panel 1 interactive rectangle controls.
5. Add panel 2 extracted texture rendering.
6. Add panel 3 spline patch rendering.
7. Add residual rendering.
8. Add optimization timer and controls: Start, Pause, Reset, Step.
9. Run tests after every meaningful change.
10. Manually verify the GUI behavior described in `docs/acceptance_tests.md`.

Do not implement a different GUI concept. The purpose is the exact three-panel prototype described here.
