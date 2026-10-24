"""Input-to-state glue for interactive play.

The controller owns the current ``State`` and asks ``Board`` for legal successors; it never
constructs a state or re-implements a transition. Ursina stays out of this module so the move logic
can be tested headless.

An input resolves to one concrete ``(next_state, action)`` pair, and that action is what the view
animates — the shape solver playback needs. On a split stage the two cubes are steered separately:
``active`` names the cube the next input moves and ``switch_cube`` hands it to the other one.

It is also the level's memory: the move count, the clock the scene ticks, a stack of the states a
move passed through (``undo``), and ``cleared`` once the block stands on the goal. Puzzle recovery —
retry and undo — lives here rather than in the views, so both are covered headless.
"""

from __future__ import annotations

from collections.abc import Callable

from bloxorz.core.contracts import Action, Direction, State
from bloxorz.core.engine import Board, roll


class PlayerController:
    def __init__(self, board: Board, block, on_goal: Callable[[], None]) -> None:
        self.board = board
        self.block = block
        self.on_goal = on_goal
        self.state: State = board.start()
        self.animating = False
        self.cleared = False
        self.moves = 0
        self.elapsed = 0.0
        self.history: list[State] = []
        self._active = 0

    @property
    def active(self) -> int:
        """Index of the cube the next input moves, or 0 while the block is unsplit."""
        return min(self._active, len(self.state.cubes) - 1)

    @property
    def split(self) -> bool:
        """Whether the block is two cubes rather than one."""
        return len(self.state.cubes) > 1

    def tick(self, dt: float) -> None:
        """Advance the level clock. The scene calls this only while the level is being played."""
        self.elapsed += dt

    def switch_cube(self) -> bool:
        """Give the next input to the other cube. Returns whether the active cube changed."""
        if self.animating or not self.split:
            return False
        self._active = 1 - self.active
        return True

    def resolve(self, direction: Direction) -> tuple[State, Action] | None:
        """The active cube's ``(next_state, action)`` in ``direction``, if there is one.

        When only the other cube can move that way the move is still offered, so a direction key is
        never dead: the active cube is a preference, not a filter. Ties go to engine order, so the
        game and solver playback pick the same action.
        """
        options = [pair for pair in self.board.successors(self.state) if pair[1][1] == direction]
        for option in options:
            if option[1][0] == self.active:
                return option
        return options[0] if options else None

    def move(self, direction: Direction) -> bool:
        """Move the active cube one action in ``direction``. Returns whether one was started."""
        if self.animating or self.cleared:
            return False
        resolved = self.resolve(direction)
        if resolved is None:
            return False

        next_state, action = resolved
        start = self.state
        self._active = self._active_after(start, next_state, action)
        self.state = next_state
        self.history.append(start)
        self.moves += 1
        self.animating = True
        self.block.animate(start, next_state, action, self._animation_finished)
        return True

    def undo(self) -> bool:
        """Take back the last move. Returns whether there was one to take back."""
        if self.animating or not self.history:
            return False
        self.state = self.history.pop()
        self.moves -= 1
        self.cleared = False
        self.block.sync(self.state)
        return True

    def retry(self) -> bool:
        """Start the level over, history and clock included. Refused while a roll is playing."""
        if self.animating:
            return False
        self.state = self.board.start()
        self.history.clear()
        self.moves = 0
        self.elapsed = 0.0
        self.cleared = False
        self._active = 0
        self.block.sync(self.state)
        return True

    @staticmethod
    def _active_after(start: State, next_state: State, action: Action) -> int:
        """Keep the cube that just moved active, even though the state re-sorts its cubes.

        ``State`` orders its cubes by cell, so one move can swap their indices; the cube is found by
        the cells it rolled onto instead. After a merge (or a teleport, which lands somewhere else
        entirely) there is nothing to follow, so the first cube takes the input.
        """
        if len(next_state.cubes) < 2:
            return 0

        index, direction = action
        moved = set(roll(start.cubes[index], direction, True) or ())
        for position, cube in enumerate(next_state.cubes):
            if moved <= set(cube):
                return position
        return 0

    def _animation_finished(self) -> None:
        self.animating = False
        if self.board.is_goal(self.state):
            self.cleared = True
            self.on_goal()
