"""Ursina prototype scene for ``L1-01``.

Deliberately bare: no title screen, menu or theme switching. The stage is loaded before the scene
is built and the window opens straight into it, playing the load animation (tiles rise, details
land on them, then the block drops in) before it accepts any input. The palette lives in
``theme.py`` and is documented in ``docs/gui/theme.md``.
"""

from __future__ import annotations

from math import cos, radians, sin
from pathlib import Path

from panda3d.core import Point2, Point3
from ursina import Entity, Text, Ursina, application, camera, held_keys, time, window
from ursina.shaders import unlit_shader

from bloxorz.core.contracts import Stage
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage

from . import dot_shader, parallax, theme
from .block_view import BlockView
from .board_view import BoardView
from .controller import PlayerController
from .intro import IntroTiming, LoadIntro
from .layout import TILE_SIZE, board_center, cell_to_world

# Low three-quarter camera matching the original game's framing: a shallow pitch,
# a small side offset, and a close enough distance to keep the platform sides visible.
CAMERA_PITCH_DEGREES = 40.0
CAMERA_YAW_DEGREES = 25.0
CAMERA_DISTANCE_FACTOR = 1.5
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


def _camera_distance(stage: Stage) -> float:
    """Distance from the framed board centre out to the camera.

    The load animation reuses it as its clearance: a piece travelling that far vertically starts
    well outside the viewport, and the value scales with the board instead of being a fixed guess.
    """
    span = max(stage.index.rows, stage.index.cols) * TILE_SIZE
    return span * CAMERA_DISTANCE_FACTOR


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
        self.board_view.refresh(self.controller.state)
        # The load animation owns the first moments of the level: it starts from the pieces'
        # resting poses and ends just before input is accepted. Travelling one camera distance
        # leaves every piece outside the window before it starts moving, however large the board.
        clearance = _camera_distance(stage)
        self.intro = LoadIntro(
            len(self.board_view.tiles),
            IntroTiming(
                tile_rise=clearance,
                obstacle_rise=clearance,
                player_drop=clearance,
            ),
            obstacle_count=len(self.board_view.details),
        )
        self._frame_camera(stage)
        self._build_hud(stage)

        # Optional presentation effects: remove either call to switch that effect off.
        self.parallax = parallax.ParallaxBackground()
        dot_shader.apply(self.board_view, self.block_view)

    def _frame_camera(self, stage: Stage) -> None:
        distance = _camera_distance(stage)
        pitch = radians(CAMERA_PITCH_DEGREES)
        yaw = radians(CAMERA_YAW_DEGREES)
        # Frame the tiles that exist, not the full grid: empty grid margins would otherwise push
        # the visible platform off to one side.
        board_x, board_z = board_center(stage)
        target = (board_x, 0.5, board_z)

        camera.fov = CAMERA_FOV
        camera.position = (
            target[0] - sin(yaw) * cos(pitch) * distance,
            target[1] + sin(pitch) * distance,
            target[2] - cos(yaw) * cos(pitch) * distance,
        )
        # Set the pose directly: look_at() introduced a small roll on this rig.
        camera.rotation = (CAMERA_PITCH_DEGREES, CAMERA_YAW_DEGREES, 0.0)
        self._align_camera_lens(stage)

    @staticmethod
    def _align_camera_lens(stage: Stage) -> None:
        """Shift the lens until the board's projected outline is centred.

        Aiming at the walkable centre removes the empty-grid margin, but the yawed perspective
        still projects the near edge wider than the far edge. A small lens shift removes that
        remaining bias without changing the camera's position or angle.
        """
        base = application.base
        cam, lens = base.cam, base.camLens
        if cam is None or lens is None:
            return

        rows, cols = stage.index.rows, stage.index.cols
        half = TILE_SIZE / 2.0
        projected_x: list[float] = []
        for row in range(rows):
            for col in range(cols):
                if stage.index.kind[row * cols + col] == "void":
                    continue
                x, z = cell_to_world((row, col), rows, cols)
                for dx in (-half, half):
                    for dz in (-half, half):
                        for y in (0.0, -theme.TILE_HEIGHT):
                            relative = cam.getRelativePoint(base.render, Point3(x + dx, y, z + dz))
                            point = Point2()
                            lens.project(relative, point)
                            projected_x.append(point.x)

        if not projected_x:
            return
        # Projection space is [-1, 1], so 0 is the window's horizontal centre. Film offset and
        # projected position move in opposite directions, so ``shift * width / 2`` cancels it.
        shift = (min(projected_x) + max(projected_x)) / 2.0
        film_x = lens.getFilmOffset().x
        lens.setFilmOffset(film_x + shift * lens.getFilmSize().x / 2.0, lens.getFilmOffset().y)

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
        if not self.intro.finished:
            self.intro.advance(time.dt)
            self.board_view.update_intro(self.intro)
            self.block_view.update_intro(self.intro)
        self.board_view.refresh(self.controller.state)
        self.board_view.update(time.dt)
        # The game only takes input once the whole load animation has played.
        if not self.intro.finished or self.controller.animating:
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
