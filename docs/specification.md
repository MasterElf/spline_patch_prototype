# Functional Specification

## 1. Window layout

The program shall open one main window with three panels:

```text
1 | 3
2 | 3
```

Panel 3 spans both rows. Use a splitter or grid layout so the user can resize panels if practical.

## 2. Coordinate systems

Use one shared reference-grid coordinate system for panels 1 and 3.

Recommended default:

- World size: 1000 x 1000 units.
- Grid line count: 20 vertical + 20 horizontal.
- Grid spacing: `world_size / (line_count - 1)` if including border lines.
- Texture coordinates: normalized `(u, v)` in `[0, 1] x [0, 1]`.

Panel views may have their own screen transforms for zooming/fitting, but math should stay in world/texture coordinates.

## 3. Panel 1: source grid and rectangle

Panel 1 shall show:

- A 20 x 20 line reference grid.
- A transformed rectangle over the grid.
- Manipulation handles.

The rectangle shall support:

- Move by dragging inside the rectangle.
- Scale by dragging corner or edge handles.
- Rotate by dragging a rotation handle outside the rectangle.

The rectangle state shall include:

- center: `(x, y)`
- width
- height
- rotation in radians or degrees

When the rectangle changes, the app shall:

1. Recompute the extracted texture representation.
2. Repaint panel 2.
3. Repaint panel 3.
4. Restart or continue the optimization using the new texture.

## 4. Panel 2: local texture view

Panel 2 shall show what is visible through the rectangle in panel 1.

Important behavior:

- Panel 2's rectangle is axis-aligned.
- The visible reference-grid line segments are transformed into local rectangle coordinates.
- If the panel 1 rectangle is rotated clockwise, grid lines in panel 2 should appear counter-rotated relative to the local rectangle.
- The resulting local line segments/intersections are the texture data used by panel 3.

Implementation note:

A raster image is not required. It is sufficient and preferred to represent the texture as:

- line segments in texture coordinates
- intersection points in texture coordinates
- a mapping from each texture intersection to its original reference-grid world point

## 5. Panel 3: target grid, spline patch, warped texture, residuals

Panel 3 shall show:

- The same reference grid as panel 1.
- A 5 x 5 spline patch control net.
- The texture from panel 2 mapped onto the spline patch.
- Residual vectors from warped texture intersections to their target reference-grid intersections.

The spline patch:

- Takes `(u, v)` texture coordinates.
- Returns a world coordinate `(x, y)`.
- Has 5 x 5 editable/optimizable control nodes.
- Should initially cover the transformed rectangle's approximate world-space area, or a reasonable default area.

The optimizer adjusts only the spline patch control nodes. It does not move the source rectangle.

## 6. Spline requirements

Use separable 2D spline evaluation:

1. For each row, interpolate the 5 control points at `u`.
2. Interpolate the resulting 5 points at `v`.

Interior segments use Catmull-Rom interpolation.

Boundary handling:

- The outer segments shall use a simpler spline that has the same derivative in the node where it meets the Catmull-Rom-defined interior.
- A practical implementation may use endpoint extrapolation or Hermite interpolation first, but isolate boundary logic so it can be improved.

## 7. Residual calculation

For each texture intersection:

1. `source_uv = texture_intersection.uv`
2. `warped_point = spline_patch.evaluate(source_uv)`
3. `target_point = texture_intersection.reference_world_point`
4. `residual = target_point - warped_point`

Total residual:

```text
sum(dot(residual, residual) for all residuals)
```

The app shall draw residual vectors in panel 3.

## 8. Hill-climb optimization

The optimizer shall:

- Keep the current best control-node positions and best residual.
- For each iteration:
  - Randomly perturb all 25 control nodes.
  - Evaluate total residual.
  - If residual improves, keep the new nodes.
  - If residual worsens, reject the perturbation.
- Run repeatedly on a GUI timer while optimization is active.
- Have a step size setting.
- Optionally reduce step size slowly when no improvement is found for many iterations.
- Never accept a worse residual in the basic hill-climb mode.

The GUI shall include basic controls:

- Start/Pause optimization.
- Reset patch.
- Single step.
- Display current residual number.
- Display iteration count and accepted-step count.

## 9. Performance expectations

This is a prototype. Prioritize correctness, clarity, and interactivity over rendering sophistication.

The app should remain usable at typical desktop sizes with:

- 20 x 20 reference grid
- 5 x 5 spline control nodes
- tens to hundreds of residual vectors

## 10. Out of scope for first version

- Loading external images.
- Saving project files.
- GPU rendering.
- Real camera/projector calibration.
- Advanced optimizer algorithms beyond the basic hill climb.
