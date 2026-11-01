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
back instead of snapping. ``snapshot``/``restore`` do the same for a whole run, which is what lets a
solver movie borrow the board and hand it back untouched.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from bloxorz.core.contracts import Action, Direction, State, Verdict
from bloxorz.core.engine import Board, orientation, roll

# The direction that rolls a move back. An undo is the same quarter-turn, mirrored.
OPPOSITE: dict[Direction, Direction] = {"U": "D", "D": "U", "L": "R", "R": "L"}

# The hole's direction from the cell that still has a tile under it.
_TIP_DIRECTIONS: dict[tuple[int, int], Direction] = {
    (0, -1): "L",
    (0, 1): "R",
    (-1, 0): "U",
    (1, 0): "D",
}


def falling_cubes(board: Board, state: State) -> frozenset[int]:
    """Which cubes of a fatal ``state`` have nothing left under them.

    On a split stage one cube can stand on a tile while the other hangs over void or a bridge that
    just closed, and only that cube drops; on an unsplit block the one piece is always the one that
    falls. Read from ``Board.passable``, so the view drops by the same rule the engine fell by.
    """
    split = len(state.cubes) == 2
    return frozenset(
        index
        for index, cube in enumerate(state.cubes)
        if not all(board.passable(cell, orientation(cube, split), state.bridges) for cell in cube)
    )


def tipping_direction(board: Board, state: State) -> Direction | None:
    """Toward the hole under half of a lying block, when that is how the fall is supported.

    Only a lying block can be half supported: a standing block or a lone cube is one cell, so it
    either stands or falls whole. A block with both cells over nothing drops straight down, so the
    answer is ``None`` there too.
    """
    if len(state.cubes) != 1 or len(state.cubes[0]) != 2:
        return None
    cube = state.cubes[0]
    piece = orientation(cube, split=False)
    grounded = [board.passable(cell, piece, state.bridges) for cell in cube]
    if grounded.count(True) != 1:
        return None
    kept, hole = cube[grounded.index(True)], cube[grounded.index(False)]
    return _TIP_DIRECTIONS[(hole[0] - kept[0], hole[1] - kept[1])]


@dataclass(frozen=True)
class Run:
    """A player's progress, held aside while solver playback borrows the board."""

    state: State
    active: int
    moves: int
    elapsed: float
    history: tuple[tuple[State, Action], ...]


class PlayerController:
    def __init__(
        self,
        board: Board,
        block,
        on_goal: Callable[[], None],
        on_loss: Callable[[], None] | None = None,
        on_drop: Callable[[], None] | None = None,
    ) -> None:
        self.board = board
        self.block = block
        self.on_goal = on_goal
        self.on_loss = on_loss
        self.on_drop = on_drop
        self.state: State = board.start()
        self.animating = False
        self.cleared = False
        self.lost = False
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

    def move(self, direction: Direction) -> bool:
        """Move the active cube one action in ``direction``. Returns whether one was started."""
        if self.animating or self.cleared or self.lost:
            return False
        choice = self._choose(direction)
        if choice is None:
            return False
        verdict, next_state, action = choice
        self.history.append((self.state, action))
        self.moves += 1
        if verdict == "fatal":
            self._begin_fatal(next_state, action)
        else:
            self._begin(next_state, action)
        return True

    def _choose(self, direction: Direction) -> tuple[Verdict, State, Action] | None:
        """The active cube's answer in ``direction``, else the other cube's.

        The active cube is a preference, not a filter: when it has nothing to do the key is handed
        to the other cube rather than dropped. Its own fall counts as something to do, so a step off
        the platform is never quietly replaced by the other cube's move. Legal actions are read from
        ``successors`` and falls from ``outcome``, so the game and playback pick the same one.
        """
        legal = {action: state for state, action in self.board.successors(self.state)}
        order = (self.active, 1 - self.active) if self.split else (self.active,)
        for index in order:
            action = (index, direction)
            if action in legal:
                return "moves", legal[action], action
            outcome = self.board.outcome(self.state, action)
            if outcome.kind == "fatal" and outcome.state is not None:
                return "fatal", outcome.state, action
        return None

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

    def _begin_fatal(self, fatal_state: State, action: Action) -> None:
        """Commit a fatal transition (fall), starting its animation."""
        start = self.state
        self.state = fatal_state
        self.lost = True
        self.animating = True
        self.block.fall(
            start,
            fatal_state,
            action,
            self._fatal_animation_finished,
            on_drop=self.on_drop,
            dropping=falling_cubes(self.board, fatal_state) or None,
            tipping=tipping_direction(self.board, fatal_state),
        )

    def _fatal_animation_finished(self) -> None:
        self.animating = False
        if self.on_loss is not None:
            self.on_loss()

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
        self.lost = False
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
        self.lost = False
        self._active = 0
        self.block.sync(self.state)
        return True

    def snapshot(self) -> Run:
        """The run as it stands, for ``restore`` after solver playback borrowed the board."""
        return Run(self.state, self.active, self.moves, self.elapsed, tuple(self.history))

    def restore(self, run: Run) -> bool:
        """Put a snapshot back exactly, view included. Refused while a roll is still playing.

        This is the way out of a solver movie: playback starts the stage over, so the player's own
        moves, clock and undo stack are put back by value rather than rolled back one by one.
        """
        if self.animating:
            return False
        self.state = run.state
        self._active = run.active
        self.moves = run.moves
        self.elapsed = run.elapsed
        self.history = list(run.history)
        self.cleared = False
        self.lost = False
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
