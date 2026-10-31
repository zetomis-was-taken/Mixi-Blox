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

from bloxorz.core.contracts import Caps, Direction, SearchResult, Stage
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage

from . import catalog, dot_shader, framing, parallax, results, theme
from .block_view import BlockView
from .board_view import BoardView
from .controller import PlayerController, Run
from .hud import Hud
from .intro import IntroTiming, LoadIntro
from .layout import TILE_SIZE, board_center, cell_to_world
from .level_select import LevelSelectScene
from .loss_overlay import LossOverlay
from .pause_overlay import PauseOverlay
from .replay import Algorithms, Replay
from .solver_menu import SolverMenu
from .solver_overlay import SolverOverlay
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

# The search runs on the one thread the window draws on, so it is given a deadline: a run that
# would take longer than this is not something a player can watch, and hitting the cap raises the
# result card with its reason instead of leaving a window that has stopped responding.
SOLVE_TIME_CAP_SECONDS = 10.0


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

    def __init__(self, stages: tuple[Stage, ...], solve: Algorithms | None = None) -> None:
        self.catalog = stages
        self.cleared: set[str] = set()
        # How a level asks for an answer. It belongs to the session, not to one transition, so the
        # next-level chain keeps the same solvers.
        self.solve = solve
        self.scene: Entity | None = None

    def show_title(self) -> None:
        self._show(TitleScene(self.show_level_select))

    def show_level_select(self) -> None:
        self._show(
            LevelSelectScene(
                self.catalog, self.cleared, self.play, on_back=self.show_title
            )
        )

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

    def __init__(self, stage: Stage, game: Game, solve: Algorithms | None = None) -> None:
        super().__init__(name="prototype")

        self.stage = stage
        self.game = game
        # Display name -> solver, in card order, or ``None`` when the level offers no Solve control.
        # Nothing else in the scene knows which algorithms exist.
        self.solve = solve
        self.board = Board(stage)
        self.board_view = BoardView(stage)
        self.board_view.root.parent = self
        self.block_view = BlockView(stage.index.rows, stage.index.cols, parent=self)
        self.controller = PlayerController(
            self.board, self.block_view, self._level_cleared, self._level_failed
        )
        self.overlay: WinOverlay | None = None
        self.loss_overlay: LossOverlay | None = None
        self.pause: PauseOverlay | None = None
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

        # Solver playback. The menu is the only way in; a replay borrows the board and the run is
        # kept aside so stopping or closing the card puts the player back exactly.
        self.panel = SolverMenu(tuple(solve), self._solve_with) if solve else None
        self.solver_overlay: SolverOverlay | None = None
        self.replay: Replay | None = None
        self.algorithm: str | None = None
        self._solved_result: SearchResult | None = None
        self._run: Run | None = None
        self._pending: str | None = None
        self._pending_delay = 0

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
        """Every action the level takes: roll, switch cube, undo, retry, pause, and playback.

        This is the whole input path, one press per action. A press is dropped — not queued — while
        the load animation plays, once the level is won, while the solver card is up, and while a
        solver movie is playing: only stop and pause are read then, so a direction key cannot
        corrupt the planned path. While the pause card is up, only its own keys are read and
        everything else is dropped. ``PlayerController`` refuses its four actions while a roll is
        still animating, so nothing arriving mid-roll survives to the next frame.
        """
        if self.pause is not None:
            self._pause_input(key)
            return
        if self.loss_overlay is not None:
            return
        if self.solver_overlay is not None or not self.intro.finished:
            return
        if self.replay is not None:
            if key == "escape":
                self._stop_replay()
            elif key == "space":
                self._toggle_pause()
            return
        if self.controller.cleared or self.controller.lost:
            return
        if key in KEY_BINDINGS:
            self.controller.move(KEY_BINDINGS[key])
        elif key == "tab":
            self.controller.switch_cube()
        elif key == "z":
            self.controller.undo()
        elif key == "r":
            self._retry()
        elif key == "escape":
            if self.panel is not None and self.panel.is_open:
                self.panel.close()
            else:
                self._pause()

    def _pause_input(self, key: str) -> None:
        """The pause card's keys, mirroring its two buttons: continue, or leave for the levels."""
        if key in ("escape", "enter"):
            self._resume()
        elif key == "l":
            self.game.show_level_select()

    def update(self) -> None:
        if self._reframe_pending:
            # One reframe per frame at most: dragging a window edge fires an event per pixel.
            self._reframe_pending = False
            self._frame_camera(self.stage)
        if self._pending is not None:
            self._run_pending()
        self.block_view.update(time.dt)
        if not self.intro.finished:
            self.intro.advance(time.dt)
            self.board_view.update_intro(self.intro)
            self.block_view.update_intro(self.intro)
        self._drive_replay(time.dt)
        self.board_view.refresh(self.controller.state)
        self.board_view.update(time.dt)
        self.block_view.set_active(self.controller.active)
        self.hud.refresh(
            self.controller.moves,
            self.controller.elapsed,
            self.controller.split,
            self.controller.active,
        )
        self.hud.show_replay(self._replay_line())
        self._show_panel_if_idle()
        # The clock runs only while the player is playing: it starts once the load animation has
        # played, stops once the block is home, and pauses while a solver movie borrows the board
        # or the pause card holds the level.
        if (
            not self.intro.finished
            or self.controller.cleared
            or self.controller.lost
            or self.replay is not None
            or self.pause is not None
            or self.loss_overlay is not None
        ):
            return
        self.controller.tick(time.dt)

    def _level_cleared(self) -> None:
        """Raise the results card: what the level cost, and the three ways out of it.

        A solver movie lands the block on the goal too, but that is not the player's clear: the
        solver card reports it, and closing that card restores the player's own run.
        """
        if self.replay is not None:
            return
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

    def _pause(self) -> None:
        """Freeze the level behind the pause card; the Solve control waits behind it too.

        A press that lands while the block is mid-roll, or while a solver run is being asked for,
        is dropped like any other press that cannot be carried out yet.
        """
        if (
            self._pending is not None
            or self.controller.animating
            or self.controller.lost
            or self.loss_overlay is not None
        ):
            return
        if self.panel is not None:
            self.panel.hide()
        self.pause = PauseOverlay(self.stage, self._resume, self.game.show_level_select)

    def _resume(self) -> None:
        """Close the pause card; the next frame puts the Solve control back if it belongs."""
        if self.pause is not None:
            destroy(self.pause)
            self.pause = None

    def _retry(self) -> None:
        """Start the level over: reset the run, then replay the load animation.

        A retry puts the stage back the way it opened — the platform re-assembles from below and the
        block drops in last — instead of the board jumping to its start pose. The camera stays where
        it is; only the pieces are re-animated.
        """
        if self.controller.retry():
            self._dismiss_overlay()
            self._dismiss_loss_overlay()
            self.intro = self._load_intro()

    def _dismiss_overlay(self) -> None:
        if self.overlay is not None:
            destroy(self.overlay)
            self.overlay = None

    def _level_failed(self) -> None:
        """Raise the loss card: retry or leave for the level select."""
        if self.replay is not None:
            return
        if self.panel is not None:
            self.panel.hide()
        self.loss_overlay = LossOverlay(
            stage=self.stage,
            on_retry=self._retry,
            on_levels=self.game.show_level_select,
        )

    def _dismiss_loss_overlay(self) -> None:
        if self.loss_overlay is not None:
            destroy(self.loss_overlay)
            self.loss_overlay = None

    def _show_panel_if_idle(self) -> None:
        """The Solve cards belong to a loaded, unsolved level that is not mid-movie."""
        if self.panel is None:
            return
        idle = (
            self.intro.finished
            and not self.controller.cleared
            and not self.controller.lost
            and self.replay is None
            and self.solver_overlay is None
            and self.pause is None
            and self.loss_overlay is None
            and self._pending is None
        )
        if idle:
            self.panel.show()
        else:
            self.panel.hide()

    def _solve_with(self, algorithm: str) -> None:
        """Ask for a run; the search itself starts on a later frame.

        The delay is deliberate: Ursina runs one thread, so a search started inside the click
        handler would freeze the window before the busy card was ever drawn.
        """
        if self.solve is None or self._pending is not None or self.replay is not None:
            return
        if self.solver_overlay is not None or not self.intro.finished or self.controller.cleared:
            return
        if self.controller.animating:
            return
        self._pending = algorithm
        self._pending_delay = 1
        if self.panel is not None:
            self.panel.set_busy(algorithm)

    def _run_pending(self) -> None:
        """Run the queued algorithm once a frame has drawn the busy card; this call blocks.

        It blocks the frame, which is why it carries a deadline: past ``SOLVE_TIME_CAP_SECONDS``
        the search returns a ``cap`` result and the card explains it.
        """
        if self._pending_delay > 0:
            self._pending_delay -= 1
            return
        algorithm, self._pending = self._pending, None
        result = self.solve[algorithm](self.stage, Caps(time_s=SOLVE_TIME_CAP_SECONDS))
        if self.panel is not None:
            self.panel.set_busy(None)
        self._start_replay(algorithm, result)

    def _start_replay(self, algorithm: str, result: SearchResult) -> None:
        """Roll the answer, or raise the card when there is no movie to play.

        A path the board cannot follow is a solver defect the scene survives: ``try_plan`` answers
        ``None``, and the card says why instead of letting the planning error out of ``update``.
        """
        replay = Replay.try_plan(self.board, result, theme.REPLAY_PAUSE_SECONDS)
        if replay is None:
            self._raise_solver_overlay(algorithm, result, note=results.UNUSABLE_PATH)
            return
        if not replay.playable:
            self._raise_solver_overlay(algorithm, result)
            return
        run = self._run if self._run is not None else self.controller.snapshot()
        if not self.controller.retry():
            return
        self._run = run
        self.algorithm = algorithm
        self._solved_result = result
        self.replay = replay
        replay.start()

    def _drive_replay(self, dt: float) -> None:
        """Feed the movie: report landings, then start the next roll once the beat is due."""
        if self.replay is None:
            return
        if not self.controller.animating and self.replay.roll_finished():
            self._finish_replay()
            return
        if self.replay.phase != "playing":
            return
        step = self.replay.advance(dt)
        if step is None:
            return
        _, next_state, action = step
        if not self.controller.play(next_state, action):
            self._stop_replay()

    def _finish_replay(self) -> None:
        """The last roll landed: report the run, leaving the player's own run behind the card."""
        result, algorithm = self._solved_result, self.algorithm
        self.replay = None
        if result is not None and algorithm is not None:
            self._raise_solver_overlay(algorithm, result)

    def _toggle_pause(self) -> None:
        if self.replay is None:
            return
        if self.replay.phase == "paused":
            self.replay.resume()
        else:
            self.replay.pause()

    def _stop_replay(self) -> None:
        """Abandon the movie and hand the board back. A stop mid-roll is dropped, like any press."""
        if self.replay is None or self.controller.animating:
            return
        self.replay = None
        self._solved_result = None
        self.algorithm = None
        self._restore_run()

    def _restore_run(self) -> None:
        """Put the player's own run back, if a solver session is holding one."""
        if self._run is not None and self.controller.restore(self._run):
            self._run = None

    def _replay_line(self) -> str | None:
        """The HUD's playback line, or ``None`` when no movie is running."""
        if self.replay is None or self.algorithm is None:
            return None
        step, total = self.replay.progress
        paused = self.replay.phase == "paused"
        return results.replay_line(self.algorithm, step, total, paused)

    def _raise_solver_overlay(
        self, algorithm: str, result: SearchResult, note: str | None = None
    ) -> None:
        """Show the outcome; "watch again" exists only when there is a path to roll.

        ``note`` replaces the detail line for a run that cannot be replayed at all, and takes the
        "watch again" card away with it: replaying it would only fail the same way.
        """
        self._dismiss_solver_overlay()
        self.algorithm = algorithm
        self._solved_result = result
        self.solver_overlay = SolverOverlay(
            stage=self.stage,
            algorithm=algorithm,
            result=result,
            on_replay=(self._replay_again if result.path and note is None else None),
            on_close=self._close_solver_overlay,
            on_levels=self.game.show_level_select,
            note=note,
        )

    def _replay_again(self) -> None:
        result, algorithm = self._solved_result, self.algorithm
        if result is None or algorithm is None:
            return
        self._dismiss_solver_overlay()
        self._start_replay(algorithm, result)

    def _close_solver_overlay(self) -> None:
        """Dismiss the card and hand the board back to the player's own run."""
        self._dismiss_solver_overlay()
        self._restore_run()
        self._solved_result = None
        self.algorithm = None

    def _dismiss_solver_overlay(self) -> None:
        if self.solver_overlay is not None:
            destroy(self.solver_overlay)
            self.solver_overlay = None

    def teardown(self) -> None:
        """Remove everything this scene put on screen: board and block are children, UI is not."""
        application.base.ignore("aspectRatioChanged")
        self.hud.teardown()
        for entity in (
            self.overlay,
            self.loss_overlay,
            self.solver_overlay,
            self.pause,
            self.panel,
            self.parallax,
        ):
            if entity is not None:
                destroy(entity)
        destroy(self)


def build(
    stage_path: str | Path | None = None,
    window_type: str = "onscreen",
    solve: Algorithms | None = None,
) -> tuple[Ursina, Game]:
    """Open the window, then boot the title screen — or ``stage_path`` when one is given.

    ``solve`` is the algorithms every level scene offers; ``None`` leaves the game exactly as it
    plays today, with no Solve control.
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


def run(stage_path: str | Path | None = None, solve: Algorithms | None = None) -> int:
    app, _ = build(stage_path, solve=solve)
    app.run()
    return 0
