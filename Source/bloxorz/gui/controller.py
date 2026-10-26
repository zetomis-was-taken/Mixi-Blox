"""Input-to-state glue for interactive play.

The controller owns the current ``State`` and asks ``Board`` for legal successors; it never
constructs a state or re-implements a transition. Ursina stays out of this module so the move logic
can be tested headless.

An input resolves to one concrete ``(next_state, action)`` pair, and that action is what the view
animates — the shape solver playback needs. ``play`` is that second caller: it applies a pair the
replay planned, as an action that costs the player nothing. On a split stage the two cubes are
steered separately: ``active`` names the cube the next input moves and ``switch_cube`` hands it to
the other one.

It is also the level's memory: the move count, the clock the scene ticks, a stack of the states a
move passed through with the action that left each one (``undo``), and ``cleared`` once the block
stands on the goal. Puzzle recovery — retry and undo — lives here rather than in the views, so both
are covered headless. An undo hands the view the same quarter-turn in reverse, so the block rolls
back instead of snapping.
"""

from __future__ import annotations

from collections.abc import Callable

from bloxorz.core.contracts import Action, Direction, State
from bloxorz.core.engine import Board, roll

# The direction that rolls a move back. An undo is the same quarter-turn, mirrored.
OPPOSITE: dict[Direction, Direction] = {"U": "D", "D": "U", "L": "R", "R": "L"}


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
        # Each entry is the state a move started from, plus the action that left it, so an undo can
        # roll that action back the same way it was played.
        self.history: list[tuple[State, Action]] = []
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
        self.history.append((self.state, action))
        self.moves += 1
        self._begin(next_state, action)
        return True

    def play(self, next_state: State, action: Action) -> bool:
        """Apply one action chosen elsewhere — solver playback — as a move that costs nothing.

        The pair comes from a ``SearchResult.path`` planned through the engine, but it is checked
        against ``Board.successors`` rather than trusted: a replay that drifted out of step with
        the board is refused here instead of rolling to a pose the board cannot reach. Playback is
        not the player's run, so ``moves``, ``elapsed`` and ``history`` stay untouched and ``Z``
        cannot take it back; reaching the goal still fires through the ordinary animation hook.
        """
        if self.animating or self.cleared:
            return False
        if (next_state, action) not in self.board.successors(self.state):
            return False
        self._begin(next_state, action)
        return True

    def _begin(self, next_state: State, action: Action) -> None:
        """Commit one legal transition and start its animation."""
        start = self.state
        self._active = self._active_after(start, next_state, action)
        self.state = next_state
        self.animating = True
        self.block.animate(start, next_state, action, self._animation_finished)

    def undo(self) -> bool:
        """Roll the last move back. Returns whether there was one to take back.

        The view is given the same action in reverse, so the block rolls its quarter-turn back
        rather than jumping: ``history`` keeps the action beside the state it started from. A
        transition a roll cannot express — a split, a merge, a teleport — is still put back by
        ``BlockView.animate`` snapping to the pose. Returns ``False`` while a roll is still playing.
        """
        if self.animating or not self.history:
            return False

        previous, action = self.history.pop()
        current = self.state
        self.state = previous
        self.moves -= 1
        self.cleared = False
        # The cube that is rolling back is the one the action moved; ``active`` follows it, and the
        # cube takes the input again in the state it is returning to.
        index = self._active_after(previous, current, action)
        self._active = action[0]
        self.animating = True
        self.block.animate(current, previous, (index, OPPOSITE[action[1]]), self._undo_finished)
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

    def _undo_finished(self) -> None:
        """The roll back is over. Stepping back can never clear a level, so nothing else follows."""
        self.animating = False
