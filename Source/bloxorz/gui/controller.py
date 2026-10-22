"""Input-to-state glue for interactive play.

The controller owns the current ``State`` and asks ``Board`` for legal successors; it never
constructs a state or re-implements a transition. Ursina stays out of this module so the move logic
can be tested headless.
"""

from __future__ import annotations

from collections.abc import Callable

from bloxorz.core.contracts import Direction, State
from bloxorz.core.engine import Board


class PlayerController:
    def __init__(self, board: Board, block, on_goal: Callable[[], None]) -> None:
        self.board = board
        self.block = block
        self.on_goal = on_goal
        self.state: State = board.start()
        self.animating = False

    def move(self, direction: Direction) -> bool:
        """Take the first legal action in ``direction``. Returns whether one was started."""
        if self.animating:
            return False

        for next_state, action in self.board.successors(self.state):
            if action[1] != direction:
                continue
            start = self.state
            self.state = next_state
            self.animating = True
            self.block.animate(start, next_state, action, self._animation_finished)
            return True

        return False

    def _animation_finished(self) -> None:
        self.animating = False
        if self.board.is_goal(self.state):
            # TODO(#28): replace this hard exit with the proper end-of-level flow
            # (results screen, next level, ...). The prototype closes the window here.
            self.on_goal()
