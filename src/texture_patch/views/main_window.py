"""Main application window.

Layout
------
    Panel 1 (top-left)  |  Panel 3 (right, spans both rows)
    Panel 2 (bot-left)  |

A horizontal QSplitter splits left vs. right.
A vertical QSplitter splits Panel 1 vs. Panel 2 on the left side.
A QTimer drives the hill-climb optimizer.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from texture_patch.geometry import RectTransform
from texture_patch.optimizer import HillClimbOptimizer, ResidualCalculator
from texture_patch.reference_grid import ReferenceGrid
from texture_patch.settings import GRID, OPT, RENDER
from texture_patch.spline_patch import SplinePatch
from texture_patch.views.panel1_source_view import Panel1SourceView
from texture_patch.views.panel2_texture_view import Panel2TextureView
from texture_patch.views.panel3_patch_view import Panel3PatchView


def _make_initial_rect() -> RectTransform:
    """Default rectangle: centred at (500, 500), 300×300, no rotation."""
    return RectTransform(
        center=np.array([500.0, 500.0]),
        width=300.0,
        height=300.0,
        rotation_radians=0.0,
    )


def _make_initial_patch(rect: RectTransform) -> SplinePatch:
    """Create a patch that covers the whole grid so the optimizer has work to do."""
    nodes = np.zeros((5, 5, 2), dtype=float)
    world_size = GRID.world_size
    for row in range(5):
        for col in range(5):
            nodes[row, col, 0] = col * world_size / 4.0
            nodes[row, col, 1] = row * world_size / 4.0
    return SplinePatch(nodes)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Texture Patch Prototype")
        self.resize(1200, 700)

        self._grid = ReferenceGrid.create_default(
            line_count=GRID.line_count, world_size=GRID.world_size
        )
        self._rect = _make_initial_rect()
        self._patch = _make_initial_patch(self._rect)
        self._texture = self._grid.extract_texture(self._rect)

        self._optimizer = HillClimbOptimizer(
            patch=self._patch,
            texture=self._texture,
            step_size=OPT.step_size,
        )

        self._is_running = False
        self._timer = QTimer(self)
        self._timer.setInterval(OPT.timer_interval_ms)
        self._timer.timeout.connect(self._on_timer_tick)

        self._build_ui()
        self._panel3.set_texture_data(self._texture)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(4)

        # ── Panels ──────────────────────────────────────────────────────
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(h_splitter, stretch=1)

        # Left column: Panel 1 on top, Panel 2 on bottom
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        h_splitter.addWidget(v_splitter)

        self._panel1 = Panel1SourceView(self._grid, self._rect)
        self._panel2 = Panel2TextureView()
        v_splitter.addWidget(self._panel1)
        v_splitter.addWidget(self._panel2)
        v_splitter.setSizes([350, 350])

        # Right column: Panel 3
        self._panel3 = Panel3PatchView(self._grid, self._patch)
        self._panel3.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        h_splitter.addWidget(self._panel3)
        h_splitter.setSizes([500, 500])

        # ── Control bar ─────────────────────────────────────────────────
        ctrl_bar = QWidget()
        ctrl_layout = QHBoxLayout(ctrl_bar)
        ctrl_layout.setContentsMargins(4, 0, 4, 4)

        self._btn_start_pause = QPushButton("Start")
        self._btn_reset = QPushButton("Reset")
        self._btn_step = QPushButton("Step")
        for btn in (self._btn_start_pause, self._btn_reset, self._btn_step):
            btn.setFixedWidth(80)
            ctrl_layout.addWidget(btn)

        ctrl_layout.addSpacing(12)

        mono = QFont("Courier New", 10)
        self._lbl_iter = QLabel("Iter: 0")
        self._lbl_accepted = QLabel("Accepted: 0")
        self._lbl_score = QLabel("Score: —")
        for lbl in (self._lbl_iter, self._lbl_accepted, self._lbl_score):
            lbl.setFont(mono)
            ctrl_layout.addWidget(lbl)

        ctrl_layout.addStretch()
        root_layout.addWidget(ctrl_bar)

        # ── Connections ─────────────────────────────────────────────────
        self._panel1.rect_transform_changed.connect(self._on_rect_changed)
        self._btn_start_pause.clicked.connect(self._on_start_pause)
        self._btn_reset.clicked.connect(self._on_reset)
        self._btn_step.clicked.connect(self._on_step)

        # Initial panel 2 content
        self._panel2.set_texture_data(self._texture)
        self._update_labels()

    # ------------------------------------------------------------------
    # Rect changed
    # ------------------------------------------------------------------

    def _on_rect_changed(self, rect: RectTransform) -> None:
        self._rect = rect
        self._texture = self._grid.extract_texture(rect)
        self._patch = _make_initial_patch(rect)

        self._optimizer.reset(self._patch, self._texture)

        self._panel2.set_texture_data(self._texture)
        self._panel3.set_patch(self._patch)
        self._panel3.set_texture_data(self._texture)
        self._update_labels()

    # ------------------------------------------------------------------
    # Optimization controls
    # ------------------------------------------------------------------

    def _on_start_pause(self) -> None:
        if self._is_running:
            self._timer.stop()
            self._is_running = False
            self._btn_start_pause.setText("Start")
        else:
            self._timer.start()
            self._is_running = True
            self._btn_start_pause.setText("Pause")

    def _on_reset(self) -> None:
        self._patch = _make_initial_patch(self._rect)
        self._optimizer.reset(self._patch, self._texture)
        self._panel3.set_patch(self._patch)
        self._update_labels()

    def _on_step(self) -> None:
        if self._texture.is_empty():
            return
        self._optimizer.step()
        self._panel3.refresh()
        self._update_labels()

    def _on_timer_tick(self) -> None:
        if self._texture.is_empty():
            return
        for _ in range(OPT.steps_per_tick):
            self._optimizer.step()
        self._panel3.refresh()
        self._update_labels()

    # ------------------------------------------------------------------
    # Status labels
    # ------------------------------------------------------------------

    def _update_labels(self) -> None:
        self._lbl_iter.setText(f"Iter: {self._optimizer.iteration}")
        self._lbl_accepted.setText(f"Accepted: {self._optimizer.accepted_count}")
        score = self._optimizer.best_score
        if score < 1e6:
            self._lbl_score.setText(f"Score: {score:.1f}")
        else:
            self._lbl_score.setText(f"Score: {score:.2e}")
