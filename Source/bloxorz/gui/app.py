"""Ursina scenes: the title screen, the level select, a playable stage, and the switch between them.

The game boots into the title screen (``TitleScene``), whose play card opens the level select
(``LevelSelectScene``), which opens a stage when a card is clicked; ``--stage`` skips both menus and
goes straight to that level. ``Game`` owns whichever scene is on screen and the session's cleared
levels, and each scene tears its own entities down before the next one is built, so no two ever
share the screen.

A level scene is deliberately bare: no theme switching. The stage is loaded before
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
    Ursina,
    application,
    camera,
    destroy,
    time,
    window,
)
from ursina.shaders import unlit_shader

from bloxorz.core.contracts import Direction, Stage
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage

from . import catalog, dot_shader, framing, parallax, theme
from .block_view import BlockView
from .board_view import BoardView
from .controller import PlayerController
from .hud import Hud
from .intro import IntroTiming, LoadIntro
from .layout import TILE_SIZE, board_center, cell_to_world
from .level_select import LevelSelectScene
from .replay import Solve
from .title import TitleScene
from .win_overlay import WinOverlay

WINDOW_TITLE = "Mixi-Blox"

# Low three-quarter camera matching the original game's framing: a shallow pitch,
# a small side offset, and a close enough distance to keep the platform sides visible.
CAMERA_PITCH_DEGREES = 40.0
CAMERA_YAW_DEGREES = 25.0
CAMERA_DISTANCE_FACTOR = 1.5
CAMERA_FOV = 45.0

# One key press, one action. Ursina delivers a press to ``input()`` as the bare key ("w"), a release
# as "w up" and a held key as "w hold"; only the bare press is bound here, so holding a direction
# never rolls twice and nothing has to be debounced.
KEY_BINDINGS: dict[str, Direction] = {
    "w": "U",
    "up arrow": "U",
    "s": "D",
    "down arrow": "D",
    "a": "L",
    "left arrow": "L",
    "d": "R",
    "right arrow": "R",
}


def _camera_distance(stage: Stage) -> float:
    """The nominal distance from the framed board centre out to the camera.

    A board is sized by its grid; ``_frame_camera`` starts here and pushes further out when the
    footprint would not fit the window. The load animation uses whatever distance the camera
    settled on as its clearance, so a piece travelling that far vertically starts outside the
    viewport, and the value scales with the board instead of being a fixed guess.
    """
    span = max(stage.index.rows, stage.index.cols) * TILE_SIZE
    return span * CAMERA_DISTANCE_FACTOR


def _projected_bounds(stage: Stage) -> tuple[float, float, float, float] | None:
    """The board footprint's ``(min_x, max_x, min_y, max_y)`` in lens space, or ``None``.

    Lens space is ``[-1, 1]`` on both axes, so 0 is the window's centre. Every corner of every
    non-void tile is projected, at the top face and at the bottom of the platform, which is the
    widest the board ever looks.
    """
    base = application.base
    cam, lens = base.cam, base.camLens
    if cam is None or lens is None:
        return None

    rows, cols = stage.index.rows, stage.index.cols
    half = TILE_SIZE / 2.0
    projected_x: list[float] = []
    projected_y: list[float] = []
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
                        projected_y.append(point.y)

    if not projected_x:
        return None
    return min(projected_x), max(projected_x), min(projected_y), max(projected_y)


class Game:
    """The scene on screen, and the levels cleared in this session."""

    def __init__(self, stages: tuple[Stage, ...], solve: Solve | None = None) -> None:
        self.catalog = stages
        self.cleared: set[str] = set()
        # How a level asks for an answer. It belongs to the session, not to one transition, so the
        # next-level chain keeps the same solver.
        self.solve = solve
        self.scene: Entity | None = None

    def show_title(self) -> None:
        self._show(TitleScene(self.show_level_select))

    def show_level_select(self) -> None:
        self._show(LevelSelectScene(self.catalog, self.cleared, self.play))

    def play(self, stage: Stage) -> None:
        self._show(PrototypeScene(stage, self, self.solve))

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

    def __init__(self, stage: Stage, game: Game, solve: Solve | None = None) -> None:
        super().__init__(name="prototype")

        self.stage = stage
        self.game = game
        # ``None`` means the scene offers no way to ask for a solution; what is built around this
        # callable is the solver panel, and until then nothing reads it.
        self.solve = solve
        self.board = Board(stage)
        self.board_view = BoardView(stage)
        self.board_view.root.parent = self
        self.block_view = BlockView(stage.index.rows, stage.index.cols, parent=self)
        self.controller = PlayerController(
            self.board, self.block_view, self._level_cleared
        )
        self.overlay: WinOverlay | None = None
        self._reframe_pending = False
        window.title = f"{WINDOW_TITLE}  |  {stage.id} {stage.name}"

        self.block_view.sync(self.controller.state)
        self.board_view.refresh(self.controller.state)
        # The camera is fitted before the load animation is built, so both use the same distance:
        # a piece travelling one camera distance starts outside the viewport, whatever the board
        # size and whatever the window's aspect ratio.
        self._frame_camera(stage)
        self.intro = self._load_intro()
        # A resize changes the vertical field of view (the horizontal one is fixed), which is what
        # decides how much of the frame the board fills, so the framing is redone when it happens.
        application.base.accept("aspectRatioChanged", self._mark_reframe)
        self.hud = Hud(stage)

        # Optional presentation effects: remove either call to switch that effect off.
        self.parallax = parallax.ParallaxBackground()
        dot_shader.apply(self.board_view, self.block_view)

    def _load_intro(self) -> LoadIntro:
        """The load timeline a level opens with: every piece rises from off-screen, block last.

        Read from the camera distance the last framing settled on, so the travel is the same
        whether the level is being opened or retried, and scales with the board and the window.
        """
        return LoadIntro(
            len(self.board_view.tiles),
            IntroTiming(
                tile_rise=self._clearance,
                obstacle_rise=self._clearance,
                player_drop=self._clearance,
            ),
            obstacle_count=len(self.board_view.details),
        )

    def _frame_camera(self, stage: Stage) -> None:
        """Frame the board for the window as it is now.

        The nominal distance comes from the grid, but a grid says nothing about how tightly the
        walkable footprint fills it, and the frame's vertical budget depends on the window's aspect
        ratio. So the camera is pushed out until ``framing`` accepts the projected outline, and the
        distance it settles on becomes ``_clearance`` for the load animation.
        """

        def measure(distance: float) -> tuple[float, float]:
            bounds = self._place_camera(stage, distance)
            if bounds is None:
                return (0.0, 0.0)
            min_x, max_x, min_y, max_y = bounds
            # The outline is centred horizontally by the lens, so its half-width is half the span;
            # vertically it is not, so the larger of the two edges is what has to fit.
            return ((max_x - min_x) / 2.0, max(abs(min_y), abs(max_y)))

        self._clearance = framing.fitting_distance(measure, _camera_distance(stage))
        self._place_camera(stage, self._clearance)

    def _place_camera(
        self, stage: Stage, distance: float
    ) -> tuple[float, float, float, float] | None:
        """Put the camera at ``distance`` and centre the outline; return the outline it sees."""
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
        return self._align_camera_lens(stage)

    @staticmethod
    def _align_camera_lens(stage: Stage) -> tuple[float, float, float, float] | None:
        """Shift the lens until the board's projected outline is centred.

        Aiming at the walkable centre removes the empty-grid margin, but the yawed perspective
        still projects the near edge wider than the far edge. A small lens shift removes that
        remaining bias without changing the camera's position or angle. The shift is a fraction of
        the film size, so it stays valid for the framing it was measured at — a resize re-measures
        it along with everything else.
        """
        lens = application.base.camLens
        if lens is None:
            return None

        # A level visited earlier already shifted the lens; this one is framed from a clean lens.
        lens.setFilmOffset(0.0, lens.getFilmOffset().y)

        bounds = _projected_bounds(stage)
        if bounds is None:
            return None
        min_x, max_x, *_ = bounds
        # Projection space is [-1, 1], so 0 is the window's horizontal centre. Film offset and
        # projected position move in opposite directions, so ``shift * width / 2`` cancels it.
        shift = (min_x + max_x) / 2.0
        film_x = lens.getFilmOffset().x
        lens.setFilmOffset(film_x + shift * lens.getFilmSize().x / 2.0, lens.getFilmOffset().y)
        # Re-measure rather than offset the numbers: the caller wants what the lens shows now.
        return _projected_bounds(stage)

    def _mark_reframe(self) -> None:
        """Ask for a reframe on the next frame; a drag-resize sends a burst of these events."""
        self._reframe_pending = True

    def input(self, key: str) -> None:
        """Every action the level takes: roll, switch cube, undo, retry.

        This is the whole input path, one press per action. A press is dropped — not queued — while
        the load animation plays or once the level is won, and ``PlayerController`` refuses the four
        actions while a roll is still animating, so nothing arriving mid-roll survives to the next
        frame.
        """
        if not self.intro.finished or self.controller.cleared:
            return
        if key in KEY_BINDINGS:
            self.controller.move(KEY_BINDINGS[key])
        elif key == "tab":
            self.controller.switch_cube()
        elif key == "z":
            self.controller.undo()
        elif key == "r":
            self._retry()

    def update(self) -> None:
        if self._reframe_pending:
            # One reframe per frame at most: dragging a window edge fires an event per pixel.
            self._reframe_pending = False
            self._frame_camera(self.stage)
        self.block_view.update(time.dt)
        if not self.intro.finished:
            self.intro.advance(time.dt)
            self.board_view.update_intro(self.intro)
            self.block_view.update_intro(self.intro)
        self.board_view.refresh(self.controller.state)
        self.board_view.update(time.dt)
        self.block_view.set_active(self.controller.active)
        self.hud.refresh(
            self.controller.moves,
            self.controller.elapsed,
            self.controller.split,
            self.controller.active,
        )
        # The clock runs only while the level is being played: it starts once the load animation has
        # played and stops once the block is home, since the overlay is modal from then on.
        if not self.intro.finished or self.controller.cleared:
            return
        self.controller.tick(time.dt)

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
        """Start the level over: reset the run, then replay the load animation.

        A retry puts the stage back the way it opened — the platform re-assembles from below and the
        block drops in last — instead of the board jumping to its start pose. The camera stays where
        it is; only the pieces are re-animated.
        """
        if self.controller.retry():
            self._dismiss_overlay()
            self.intro = self._load_intro()

    def _dismiss_overlay(self) -> None:
        if self.overlay is not None:
            destroy(self.overlay)
            self.overlay = None

    def teardown(self) -> None:
        """Remove everything this scene put on screen: board and block are children, UI is not."""
        application.base.ignore("aspectRatioChanged")
        self.hud.teardown()
        for entity in (self.overlay, self.parallax):
            if entity is not None:
                destroy(entity)
        destroy(self)


def build(
    stage_path: str | Path | None = None,
    window_type: str = "onscreen",
    solve: Solve | None = None,
) -> tuple[Ursina, Game]:
    """Open the window, then boot the title screen — or ``stage_path`` when one is given.

    ``solve`` is the solver every level scene is offered; ``None`` leaves the game exactly as it
    plays today, with no way to ask for a solution.
    """
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

    game = Game(catalog.load_catalog(), solve)
    if stage_path is None:
        game.show_title()
    else:
        game.play(load_stage(stage_path))
    return app, game


def run(stage_path: str | Path | None = None, solve: Solve | None = None) -> int:
    app, _ = build(stage_path, solve=solve)
    app.run()
    return 0
