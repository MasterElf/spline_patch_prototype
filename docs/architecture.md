# Suggested Architecture

## Data flow

```text
Panel 1 rectangle transform
        |
        v
ReferenceGrid.extract_texture(rect_transform)
        |
        v
TextureData
        |
        +----> Panel 2 renders local texture
        |
        v
SplinePatch + HillClimbOptimizer
        |
        v
Panel 3 renders grid, warped texture, residuals
```

## Suggested classes

### `RectTransform`

Location: `src/texture_patch/geometry.py`

Responsibilities:

- Store center, width, height, rotation.
- Convert between normalized local coordinates and world coordinates.
- Return world-space corners.
- Test whether a world point is inside the rectangle.

Expected methods:

```python
local_to_world(uv: ArrayLike) -> np.ndarray
world_to_local(point: ArrayLike) -> np.ndarray
corners_world() -> np.ndarray
contains_world(point: ArrayLike) -> bool
```

### `ReferenceGrid`

Location: `src/texture_patch/reference_grid.py`

Responsibilities:

- Generate grid line segments and grid intersections.
- Extract the parts visible inside a transformed rectangle.
- Produce `TextureData`.

Expected methods:

```python
create_default() -> ReferenceGrid
extract_texture(rect_transform: RectTransform) -> TextureData
```

### `TextureData`

Location: `src/texture_patch/reference_grid.py`

Responsibilities:

- Store local texture line segments.
- Store local texture intersections.
- Preserve mapping from texture intersections to reference-grid world intersections.

Suggested fields:

```python
line_segments_uv: list[LineSegment]
intersections: list[TextureIntersection]
```

### `SplinePatch`

Location: `src/texture_patch/spline_patch.py`

Responsibilities:

- Store a 5 x 5 control-node array.
- Evaluate world-space point from `(u, v)`.
- Copy/update nodes for optimization.

Expected methods:

```python
create_default(world_rect: RectTransform | None = None) -> SplinePatch
evaluate(uv: ArrayLike) -> np.ndarray
evaluate_many(uvs: np.ndarray) -> np.ndarray
copy_nodes() -> np.ndarray
set_nodes(nodes: np.ndarray) -> None
```

### `ResidualCalculator`

Location: `src/texture_patch/optimizer.py`

Responsibilities:

- Compute residual vectors between texture intersections and target reference points.
- Compute total sum-of-squares residual.

Expected methods:

```python
compute_residuals(patch: SplinePatch, texture: TextureData) -> list[Residual]
compute_total_residual(patch: SplinePatch, texture: TextureData) -> float
```

### `HillClimbOptimizer`

Location: `src/texture_patch/optimizer.py`

Responsibilities:

- Perturb all patch nodes each iteration.
- Accept only improved states.
- Track best score and iteration counters.

Expected methods:

```python
reset(patch: SplinePatch, texture: TextureData) -> None
step() -> OptimizationStepResult
```

## GUI

Use three custom `QWidget` subclasses:

- `Panel1SourceView`
- `Panel2TextureView`
- `Panel3PatchView`

Use Qt signals for updates:

```text
Panel1SourceView.rect_transform_changed
        -> MainWindow updates model
        -> Panel2TextureView.set_texture_data(...)
        -> Panel3PatchView.set_texture_data(...)
        -> optimizer.reset(...)
```

Use a `QTimer` in `MainWindow` for optimization. Each timer tick can run several optimizer steps, then repaint panel 3.

## Rendering guidance

Use `QPainter`.

Panel 1:

- Draw grid.
- Draw transformed rectangle.
- Draw handles.
- Use anti-aliasing.

Panel 2:

- Draw a rectangular texture area.
- Convert UV to widget coordinates.
- Draw texture line segments.

Panel 3:

- Draw reference grid.
- Draw spline control net.
- Draw warped texture by sampling texture line segments and mapping sampled UV points through the spline patch.
- Draw residual vectors.

## Warping texture line segments

For each texture line segment `(uv0, uv1)`:

1. Sample N points between `uv0` and `uv1`.
2. Evaluate each point through `SplinePatch.evaluate`.
3. Draw a polyline in panel 3.

Use 16 or 32 samples per segment for the first version.
