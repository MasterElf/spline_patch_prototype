# Spline Patch Texture Alignment Prototype

This repository is a Claude Code starter package for building a Python/PySide6 prototype.

The target program has three panels:

```text
1 | 3
2 | 3
```

- Panel 1: reference grid + movable/rotatable/scalable rectangle.
- Panel 2: texture extracted from the rectangle, shown in rectangle-local coordinates.
- Panel 3: reference grid + spline patch + mapped texture + residual vectors + hill-climb optimization.

## Start with Claude Code

Open a terminal in this folder and run:

```bash
claude
```

Then paste the contents of:

```text
prompts/build_program.md
```

## Manual Python setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest
python -m texture_patch.app
```

## Main documents

- `CLAUDE.md`: project instructions Claude Code should follow.
- `docs/specification.md`: detailed behavior specification.
- `docs/architecture.md`: suggested design.
- `docs/acceptance_tests.md`: manual acceptance tests.
- `prompts/build_program.md`: prompt to paste into Claude Code.
