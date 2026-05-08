# Acceptance Tests

These tests are meant for Claude Code and for manual verification.

## Automated tests

Claude shall run:

```bash
python -m pytest
```

All tests in `tests/` must pass.

## Manual GUI tests

### Test 1: App starts

1. Run `python -m texture_patch.app`.
2. Verify that one main window opens.
3. Verify the layout is:

```text
1 | 3
2 | 3
```

Expected result:

- Panel 1 is top-left.
- Panel 2 is bottom-left.
- Panel 3 spans both rows on the right.

### Test 2: Panel 1 grid and rectangle

1. Look at panel 1.
2. Verify that a 20 x 20 line grid is visible.
3. Verify that a rectangle is visible on top of the grid.

Expected result:

- Grid lines are stable.
- Rectangle is clearly visible.
- Handles are visible or discoverable.

### Test 3: Move rectangle

1. Drag inside the rectangle in panel 1.
2. Move it across the reference grid.

Expected result:

- Rectangle moves.
- Panel 2 changes immediately.
- Panel 3 changes immediately.
- Residuals update.

### Test 4: Rotate rectangle

1. Drag the rotation handle in panel 1.
2. Rotate the rectangle roughly 30 degrees.

Expected result:

- Rectangle rotates in panel 1.
- Panel 2 still shows an axis-aligned rectangle.
- Grid lines inside panel 2 become slanted.
- Panel 3 updates the mapped texture.

### Test 5: Scale rectangle

1. Drag a corner or edge handle in panel 1.
2. Make the rectangle larger and smaller.

Expected result:

- Rectangle scales.
- Panel 2 shows more or less of the reference grid.
- Panel 3 updates.

### Test 6: Optimization runs

1. Press Start.
2. Observe panel 3.

Expected result:

- Spline patch control nodes should visibly jitter/adjust.
- The residual number should generally decrease over time.
- Worse steps must not be accepted by the basic hill-climb optimizer.
- Residual vectors should be drawn above the grid/texture.

### Test 7: Pause and step

1. Press Pause.
2. Record the current iteration count.
3. Press Step once.

Expected result:

- The iteration count increases by one.
- The patch changes only if the step improves the residual.
- The score never worsens after an accepted step.

### Test 8: Reset patch

1. Press Reset.
2. Observe panel 3.

Expected result:

- The spline patch returns to its default position.
- Iteration counters reset or clearly indicate a new run.
- Optimization can start again.

### Test 9: No crash on extreme transforms

1. Move the rectangle partially outside the grid.
2. Make it narrow, wide, and rotated.
3. Start optimization.

Expected result:

- The app does not crash.
- If no useful intersections exist, the GUI displays a clear neutral state.
- Optimizer should skip or report no residual data instead of failing.
