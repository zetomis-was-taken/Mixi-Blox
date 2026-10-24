"""Ursina scenes: the level select, a playable stage, and the switch between them.

The game boots into the level select (``LevelSelectScene``) and opens a stage when a card is
clicked; ``--stage`` skips straight to that level. ``Game`` owns whichever scene is on screen and
the session's cleared levels, and each scene tears its own entities down before the next one is
built, so the two never share the screen.

A level scene is deliberately bare: no title screen or theme switching. The stage is loaded before
the scene is built and plays the load animation (tiles rise, details land on them, then the block
drops in) before it accepts any input. Landing on the goal raises ``WinOverlay``, which offers the
next level, a retry and the way back to the level select. The palette lives in ``theme.py`` and is
documented in ``docs/gui/theme.md``.
"""

from __future__ import annotations

from math import cos, radians, sin
from pathlib import Path

from panda3d.core import Point2, Point3
from ursina import (
    Entity,
    Text,
    Ursina,
    application,
    camera,
    destroy,
    held_keys,
    time,
    window,
)
from ursina.shaders import unlit_shader

from bloxorz.core.contracts import Stage
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage

from . import catalog, dot_shader, parallax, theme
from .block_view import BlockView
from .board_view import BoardView
from .controller import PlayerController
from .intro import IntroTiming, LoadIntro
from .layout import TILE_SIZE, board_center, cell_to_world
from .level_select import LevelSelectScene
from .win_overlay import WinOverlay

WINDOW_TITLE = "Mixi-Blox"

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

ROLL_HINT = "WASD / arrow keys to roll"
ACTION_HINT = "Z undo   |   R retry"


def _camera_distance(stage: Stage) -> float:
    """Distance from the framed board centre out to the camera.

    The load animation reuses it as its clearance: a piece travelling that far vertically starts
    well outside the viewport, and the value scales with the board instead of being a fixed guess.
    """
    span = max(stage.index.rows, stage.index.cols) * TILE_SIZE
    return span * CAMERA_DISTANCE_FACTOR


class Game:
    """The scene on screen, and the levels cleared in this session."""

    def __init__(self, stages: tuple[Stage, ...]) -> None:
        self.catalog = stages
        self.cleared: set[str] = set()
        self.scene: Entity | None = None

    def show_level_select(self) -> None:
        self._show(LevelSelectScene(self.catalog, self.cleared, self.play))

    def play(self, stage: Stage) -> None:
        self._show(PrototypeScene(stage, self))

    def level_cleared(self, stage: Stage) -> None:
        """Remember a cleared level so the level select can show it."""
        self.cleared.add(stage.id)

    def _show(self, scene: Entity) -> None:
        """Replace the scene on screen: the old one clears its entities, then the new one builds."""
        if self.scene is not None:
            self.scene.teardown()
        self.scene = scene


class PrototypeScene(Entity):
    """The scene's update owner. ``Ursina`` itself is a singleton and cannot be subclassed."""

    def __init__(self, stage: Stage, game: Game) -> None:
        super().__init__(name="prototype")

        self.stage = stage
        self.game = game
        self.board = Board(stage)
        self.board_view = BoardView(stage)
        self.board_view.root.parent = self
        self.block_view = BlockView(stage.index.rows, stage.index.cols, parent=self)
        self.controller = PlayerController(
            self.board, self.block_view, self._level_cleared
        )
        self.overlay: WinOverlay | None = None
        window.title = f"{WINDOW_TITLE}  |  {stage.id} {stage.name}"

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
        self.hud_texts = self._build_hud(stage)

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

        # A level visited earlier already shifted the lens; this one is framed from a clean lens.
        lens.setFilmOffset(0.0, lens.getFilmOffset().y)

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

    def _build_hud(self, stage: Stage) -> tuple[Text, Text, Text]:
        """The level name, what the keys do, and — on a split stage — which cube moves next."""
        title = Text(
            text=f"{stage.id}  {stage.name}",
            position=(-0.78, 0.47),
            origin=(-0.5, 0.5),
            color=theme.TEXT,
        )
        keys = Text(
            text=f"{ROLL_HINT}   |   {ACTION_HINT}",
            position=(-0.78, 0.43),
            origin=(-0.5, 0.5),
            color=theme.TEXT,
            scale=0.8,
        )
        # Only a split stage has a second cube to steer, so this line stays hidden otherwise.
        cube = Text(
            position=(-0.78, 0.39),
            origin=(-0.5, 0.5),
            color=theme.TEXT,
            scale=0.8,
        )
        return title, keys, cube

    def _refresh_hud(self) -> None:
        """Show which cube the next input moves, matching the tint in ``BlockView``."""
        cube = self.hud_texts[2]
        cube.enabled = self.controller.split
        if self.controller.split:
            cube.text = f"Cube {self.controller.active + 1} of 2  |  Tab to switch"

    def input(self, key: str) -> None:
        """Action keys: switch cube, undo, retry. The overlay owns input once the level is won."""
        if not self.intro.finished or self.controller.cleared:
            return
        if key == "tab":
            self.controller.switch_cube()
        elif key == "z":
            self.controller.undo()
        elif key == "r":
            self.controller.retry()

    def update(self) -> None:
        self.block_view.update(time.dt)
        if not self.intro.finished:
            self.intro.advance(time.dt)
            self.board_view.update_intro(self.intro)
            self.block_view.update_intro(self.intro)
        self.board_view.refresh(self.controller.state)
        self.board_view.update(time.dt)
        self.block_view.set_active(self.controller.active)
        self._refresh_hud()
        # The game only takes input once the whole load animation has played, and stops again once
        # the level is cleared: the overlay is modal from then on.
        if not self.intro.finished or self.controller.cleared:
            return
        self.controller.tick(time.dt)
        if self.controller.animating:
            return

        for key, direction in KEY_BINDINGS:
            if held_keys[key]:
                self.controller.move(direction)
                break

    def _level_cleared(self) -> None:
        """Raise the results card: what the level cost, and the three ways out of it."""
        self.game.level_cleared(self.stage)
        following = catalog.next_stage(self.game.catalog, self.stage)
        self.overlay = WinOverlay(
            stage=self.stage,
            moves=self.controller.moves,
            seconds=self.controller.elapsed,
            on_next=(lambda: self.game.play(following)) if following is not None else None,
            on_retry=self._retry,
            on_levels=self.game.show_level_select,
        )

    def _retry(self) -> None:
        """Start this level over from the overlay's retry card."""
        if self.controller.retry():
            self._dismiss_overlay()

    def _dismiss_overlay(self) -> None:
        if self.overlay is not None:
            destroy(self.overlay)
            self.overlay = None

    def teardown(self) -> None:
        """Remove everything this scene put on screen: board and block are children, UI is not."""
        for entity in (*self.hud_texts, self.overlay, self.parallax):
            if entity is not None:
                destroy(entity)
        destroy(self)


def build(
    stage_path: str | Path | None = None, window_type: str = "onscreen"
) -> tuple[Ursina, Game]:
    """Open the window, then boot the level select — or ``stage_path`` when one is given."""
    app = Ursina(
        title=WINDOW_TITLE,
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

    game = Game(catalog.load_catalog())
    if stage_path is None:
        game.show_level_select()
    else:
        game.play(load_stage(stage_path))
    return app, game


def run(stage_path: str | Path | None = None) -> int:
    app, _ = build(stage_path)
    app.run()
    return 0
