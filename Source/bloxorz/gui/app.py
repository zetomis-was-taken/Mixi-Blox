"""Ursina prototype scene for ``L1-01``.

Deliberately bare: no title screen, menu, loading state or theme. The stage is loaded before the
scene is built and the window opens straight into it. A later ``theme.md`` replaces the palette in
``theme.py``; nothing here guesses an art direction.
"""

from __future__ import annotations

from math import cos, radians, sin
from pathlib import Path

from ursina import Entity, Text, Ursina, application, camera, held_keys, time, window
from ursina.shaders import unlit_shader

from bloxorz.core.contracts import Stage
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage

from . import theme
from .block_view import BlockView
from .board_view import BoardView
from .controller import PlayerController
from .layout import TILE_SIZE

# Low three-quarter camera matching the original game's framing: a shallow pitch,
# a small side offset, and a close enough distance to keep the platform sides visible.
CAMERA_PITCH_DEGREES = 45.0
CAMERA_YAW_DEGREES = 25.0
CAMERA_DISTANCE_FACTOR = 1.25
CAMERA_FOV = 45.0

KEY_BINDINGS: tuple[tuple[str, str], ...] = (
    ("w", "U"),
    ("up arrow", "U"),
    ("s", "D"),
    ("down arrow", "D"),
    ("a", "L"),
    ("left arrow", "L"),
    ("d", "R"),
    ("right arrow", "R"),
)


class PrototypeScene(Entity):
    """The scene's update owner. ``Ursina`` itself is a singleton and cannot be subclassed."""

    def __init__(self, stage: Stage) -> None:
        super().__init__(name="prototype")

        self.stage = stage
        self.board = Board(stage)
        self.board_view = BoardView(stage)
        self.block_view = BlockView(stage.index.rows, stage.index.cols)
        self.controller = PlayerController(
            self.board, self.block_view, self._level_cleared
        )

        self.block_view.sync(self.controller.state)
        self.board_view.refresh(self.controller.state.bridges)
        self._frame_camera(stage)
        self._build_hud(stage)

    def _frame_camera(self, stage: Stage) -> None:
        span = max(stage.index.rows, stage.index.cols) * TILE_SIZE
        distance = span * CAMERA_DISTANCE_FACTOR
        pitch = radians(CAMERA_PITCH_DEGREES)
        yaw = radians(CAMERA_YAW_DEGREES)
        target = (0, 0.5, 0)

        camera.fov = CAMERA_FOV
        camera.position = (
            -sin(yaw) * cos(pitch) * distance,
            target[1] + sin(pitch) * distance,
            -cos(yaw) * cos(pitch) * distance,
        )
        # Set the pose directly: look_at() introduced a small roll on this rig.
        camera.rotation = (CAMERA_PITCH_DEGREES, CAMERA_YAW_DEGREES, 0.0)

    def _build_hud(self, stage: Stage) -> None:
        Text(
            text=f"{stage.id}  {stage.name}",
            position=(-0.78, 0.47),
            origin=(-0.5, 0.5),
            color=theme.TEXT,
        )
        Text(
            text="WASD / arrow keys to roll",
            position=(-0.78, 0.43),
            origin=(-0.5, 0.5),
            color=theme.TEXT,
            scale=0.8,
        )

    def update(self) -> None:
        self.block_view.update(time.dt)
        self.board_view.refresh(self.controller.state.bridges)
        if self.controller.animating:
            return

        for key, direction in KEY_BINDINGS:
            if held_keys[key]:
                self.controller.move(direction)
                break

    def _level_cleared(self) -> None:
        # TODO(#28): replace this hard exit with a proper end-of-level flow
        # (results screen, next level, ...). The prototype must close immediately.
        application.quit()


def build(
    stage_path: str | Path, window_type: str = "onscreen"
) -> tuple[Ursina, PrototypeScene]:
    """Load a stage, open the window, and construct the scene. Used by ``run`` and smoke tests."""
    stage = load_stage(stage_path)
    app = Ursina(
        title=f"Mixi-Blox  |  {stage.id} {stage.name}",
        borderless=False,
        fullscreen=False,
        size=(1280, 800),
        development_mode=False,
        editor_ui_enabled=False,
        window_type=window_type,
    )

    # Flat silhouettes: no lights, no fog, no shadows.
    Entity.default_shader = unlit_shader
    window.color = theme.BACKGROUND

    return app, PrototypeScene(stage)


def run(stage_path: str | Path) -> int:
    app, _ = build(stage_path)
    app.run()
    return 0
