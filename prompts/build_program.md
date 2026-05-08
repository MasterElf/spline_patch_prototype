Read `CLAUDE.md`, `docs/specification.md`, `docs/architecture.md`, `docs/implementation_plan.md`, and `docs/acceptance_tests.md`.

Build the described Python/PySide6 prototype in this repository.

Important constraints:

1. Implement the actual three-panel application. Do not replace it with a simpler demo.
2. Keep math and GUI separated.
3. Start by implementing the pure math modules and make all pytest tests pass.
4. Then implement the GUI and connect it to the same math model.
5. Use vector-rendered grid lines and texture line segments. Do not introduce image files unless there is a strong reason.
6. Panel 1 must contain an interactive transformed rectangle.
7. Panel 2 must show the visible grid through the rectangle in rectangle-local coordinates.
8. Panel 3 must show the same reference grid, a 5 x 5 spline patch, the texture mapped onto the patch, and residual vectors.
9. Add Start/Pause, Reset, and Step controls for the hill-climb optimizer.
10. Run `python -m pytest` before finishing. Fix any failures.
11. Keep comments in English.
12. Use clear, maintainable Python with type hints.

When done, report:

- how to run the app
- how to run the tests
- which acceptance tests you manually checked or could not check
- any limitations in the first version
