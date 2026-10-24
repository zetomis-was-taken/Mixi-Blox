"""Input-to-state glue for interactive play.

The controller owns the current ``State`` and asks ``Board`` for legal successors; it never
constructs a state or re-implements a transition. Ursina stays out of this module so the move logic
can be tested headless.

An input resolves to one concrete ``(next_state, action)`` pair, and that action is what the view
animates — the shape solver playback needs. On a split stage the two cubes are steered separately:
``active`` names the cube the next input moves and ``switch_cube`` hands it to the other one.
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
        self._active = 0

    @property
    def active(self) -> int:
        """Index of the cube the next input moves, or 0 while the block is unsplit."""
        return min(self._active, len(self.state.cubes) - 1)

    @property
    def split(self) -> bool:
        """Whether the block is two cubes rather than one."""
        return len(self.state.cubes) > 1

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
        if self.animating:
            return False
        resolved = self.resolve(direction)
        if resolved is None:
            return False

        next_state, action = resolved
        start = self.state
        self._active = self._active_after(start, next_state, action)
        self.state = next_state
        self.animating = True
        self.block.animate(start, next_state, action, self._animation_finished)
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
            # TODO(#28): replace this hard exit with the proper end-of-level flow
            # (results screen, next level, ...). The prototype closes the window here.
            self.on_goal()
