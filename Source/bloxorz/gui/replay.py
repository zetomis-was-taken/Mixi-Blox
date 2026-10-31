"""Playback of a solved path: one action at a time, one roll in flight.

A solver answers with a ``SearchResult`` whose ``path`` is a tuple of actions. This module turns
that tuple into the state-to-state transitions the view already animates, and paces them. It knows
nothing about Ursina and nothing about roll length: the scene asks for the next step, the view
reports that its roll landed, and the only duration measured here is the pause between two rolls.

The sequence is planned once, at construction, by asking ``Board.successors`` for each action in
turn — the same way ``PlayerController`` gets its moves, so no transition is re-implemented and a
path that is not legal raises here rather than surfacing later as a block that snapped to the wrong
tile. A result that is not ``solved`` has nothing to play, and neither has a solved one whose path
is empty (the start already satisfies the goal); both finish immediately with ``playable`` false,
which is the scene's cue to show a results card instead of a movie.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Literal

from bloxorz.core.contracts import Action, Caps, SearchResult, Stage, State
from bloxorz.core.engine import Board

Phase = Literal["ready", "playing", "paused", "finished", "aborted"]
# What the view animates: where the roll starts, where it lands, and the action between them.
Step = tuple[State, State, Action]
# How the GUI asks for an answer: the frozen ``solve`` signature of ``docs/contracts.md``.
Solve = Callable[[Stage, Caps], SearchResult]
# What the Solve control offers: display name -> solver, in card order.
Algorithms = Mapping[str, Solve]


class Replay:
    """One solver answer, planned into steps and handed out one roll at a time."""

    def __init__(
        self,
        board: Board,
        result: SearchResult,
        pause: float,
        *,
        restore: State | None = None,
    ) -> None:
        self.board = board
        self.result = result
        self.pause_seconds = pause
        self.origin = board.start()
        # What ``stop`` hands back: the state the scene was in before the solve was asked for. A
        # replay always plays the stage from its start, so by default that is the start itself.
        self.restore = self.origin if restore is None else restore
        self.steps: tuple[Step, ...] = (
            self._plan(result.path) if result.status == "solved" else ()
        )
        self.playable = bool(self.steps)
        self.phase: Phase = "ready" if self.playable else "finished"
        self.index = 0
        self._in_flight = False
        self._since_step = 0.0
        self._speed = 1.0

    @classmethod
    def try_plan(
        cls,
        board: Board,
        result: SearchResult,
        pause: float,
        *,
        restore: State | None = None,
    ) -> Replay | None:
        """Plan a replay, or ``None`` when the solver's path cannot be followed.

        A path the board cannot follow is a defect in the solver, not a reason to take the frame
        loop down with it: the scene shows the result card with a note instead. ``Replay`` itself
        still raises, so a caller that wants the error keeps it.
        """
        try:
            return cls(board, result, pause, restore=restore)
        except ValueError:
            return None

    @property
    def speed(self) -> float:
        return self._speed

    @property
    def progress(self) -> tuple[int, int]:
        """``(steps started, steps planned)`` for the HUD's "move k of n" line."""
        return self.index, len(self.steps)

    @property
    def remaining(self) -> int:
        return len(self.steps) - self.index

    def set_speed(self, speed: float) -> None:
        """Scale the pause only: the roll's own length stays the view's business."""
        if speed <= 0.0:
            raise ValueError("playback speed must be positive")
        self._speed = speed

    def start(self) -> bool:
        """Begin playback. Only a freshly planned replay starts; a resumed one uses ``resume``."""
        if self.phase != "ready":
            return False
        self.phase = "playing"
        return True

    def pause(self) -> bool:
        if self.phase != "playing":
            return False
        self.phase = "paused"
        return True

    def resume(self) -> bool:
        if self.phase != "paused":
            return False
        self.phase = "playing"
        return True

    def stop(self) -> State:
        """Abandon playback and hand the scene the state to put back.

        A stop is final — no more steps — so watching again rebuilds a fresh replay. A replay that
        already finished stays finished; stopping it changes nothing.
        """
        if self.phase != "finished":
            self.phase = "aborted"
        return self.restore

    def advance(self, dt: float) -> Step | None:
        """Tick the pause and return the next step once it is due, or ``None``.

        Only one step is ever in flight: while a roll is playing ``advance`` hands out nothing, so
        the scene never has to defend against overlapping animations. The first step starts at
        once; later ones wait ``pause_seconds`` (divided by the speed) after the previous roll
        landed.
        """
        if self.phase != "playing" or self._in_flight:
            return None
        if self.index >= len(self.steps):
            self.phase = "finished"
            return None
        if self.index > 0:
            self._since_step += dt
            if self._since_step < self.pause_seconds / self._speed:
                return None

        self._since_step = 0.0
        step = self.steps[self.index]
        self.index += 1
        self._in_flight = True
        return step

    def roll_finished(self) -> bool:
        """The view landed the roll it was given. Returns whether that was the last one."""
        if not self._in_flight:
            return False
        self._in_flight = False
        if self.phase not in ("playing", "paused") or self.index < len(self.steps):
            return False
        self.phase = "finished"
        return True

    def _plan(self, path: tuple[Action, ...]) -> tuple[Step, ...]:
        """Follow ``path`` through the engine, one legal successor at a time."""
        steps: list[Step] = []
        state = self.origin
        for action in path:
            following = next(
                (pair for pair in self.board.successors(state) if pair[1] == action), None
            )
            if following is None:
                raise ValueError(f"{action} is not legal from {state.key()}")
            next_state, _ = following
            steps.append((state, next_state, action))
            state = next_state
        return tuple(steps)
