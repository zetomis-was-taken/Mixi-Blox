"""``Board``: the stage-scoped transition model (§ Board).

Transitions need stage data a state does not carry, so they hang off a board built from one stage.
``Board(stage)`` is O(1): the lookup tables were compiled by ``load_stage``.
"""

from __future__ import annotations

from bloxorz.core.contracts import (
    Action,
    Cell,
    Cube,
    Direction,
    Kind,
    Orientation,
    Outcome,
    Stage,
    State,
    Verdict,
)

DIRECTIONS: tuple[Direction, ...] = ("U", "D", "L", "R")


def cells(state: State) -> tuple[Cell, ...]:
    """Every occupied cell, one cube at a time. The only sanctioned way to ask (§ Values)."""
    return tuple(cell for cube in state.cubes for cell in cube)


def pivot(state: State) -> Cell:
    """The lexicographically smaller occupied cell (§ Values)."""
    return min(cells(state))


def orientation(cube: Cube, split: bool) -> Orientation:
    """Derive the piece's orientation from its cells. Never stored (§ Values)."""
    if len(cube) == 2:
        return "lying_h" if cube[0][0] == cube[1][0] else "lying_v"
    return "cube" if split else "standing"


def roll(cube: Cube, direction: Direction, split: bool) -> Cube | None:
    """Roll one piece one action. Returns the new cells, sorted; ``None`` only for a bad index."""
    if len(cube) == 1:
        row, col = cube[0]
        if split:
            step = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}[direction]
            return ((row + step[0], col + step[1]),)
        if direction == "U":
            return ((row - 2, col), (row - 1, col))
        if direction == "D":
            return ((row + 1, col), (row + 2, col))
        if direction == "L":
            return ((row, col - 2), (row, col - 1))
        return ((row, col + 1), (row, col + 2))
    if cube[0][0] == cube[1][0]:
        row, left = cube[0][0], cube[0][1]
        if direction == "L":
            return ((row, left - 1),)
        if direction == "R":
            return ((row, left + 2),)
        if direction == "U":
            return ((row - 1, left), (row - 1, left + 1))
        return ((row + 1, left), (row + 1, left + 1))
    top, col = cube[0][0], cube[0][1]
    if direction == "U":
        return ((top - 1, col),)
    if direction == "D":
        return ((top + 2, col),)
    if direction == "L":
        return ((top, col - 1), (top + 1, col - 1))
    return ((top, col + 1), (top + 1, col + 1))


def _after_mode(action: str | None, is_open: bool) -> bool:
    """Apply one of the original's three bridge modes: `on` opens, `off` closes, `toggle` inverts.

    The mode is data, so a heavy switch may open a bridge and a soft one may close it. What a tile's
    *type* decides is who fires it, not what it does.
    """
    if action == "on":
        return True
    if action == "off":
        return False
    return not is_open


def _merge(cubes: list[Cube]) -> list[Cube]:
    """Merge two orthogonally adjacent cubes into one lying block, along their axis (ADR-007)."""
    if len(cubes) != 2 or len(cubes[0]) != 1 or len(cubes[1]) != 1:
        return cubes
    (row_a, col_a), (row_b, col_b) = cubes[0][0], cubes[1][0]
    same_row = row_a == row_b and abs(col_a - col_b) == 1
    same_col = col_a == col_b and abs(row_a - row_b) == 1
    if same_row or same_col:
        return [tuple(sorted((cubes[0][0], cubes[1][0])))]
    return cubes


class Board:
    """The transitions of one stage. Immutable after construction, shared across solvers."""

    def __init__(self, stage: Stage) -> None:
        self._stage = stage
        self._index = stage.index

    def start(self) -> State:
        """The state a stage begins in: standing on ``S``, every bridge as the file declares it."""
        return State(
            cubes=((self._index.start,),),
            bridges=tuple(bridge.initially_open for bridge in self._stage.bridges),
        )

    def successors(self, state: State) -> list[tuple[State, Action]]:
        """Every legal action from ``state``, as ``(next_state, (cube_index, direction))``.

        Illegal actions are absent, not generated-and-lost: void, a closed bridge, two cubes on one
        cell, a move that would park the block over a bridge the same action closes (ADR-005), and
        a standing block on fragile (ADR-003).

        Absent here means absent from *search*. Two of those refusals are not walls to a player —
        a fragile tile breaks, and a bridge closes under the block — and ``outcome`` reports them
        as fatal. This keeps only `moves`, so the reachable state set is unchanged.
        """
        found: list[tuple[State, Action]] = []
        for index in range(len(state.cubes)):
            for direction in DIRECTIONS:
                verdict, next_state = self._resolve(state, index, direction)
                if verdict == "moves" and next_state is not None:
                    found.append((next_state, (index, direction)))
        return found

    def outcome(self, state: State, action: Action) -> Outcome:
        """What one pressed action does: it moves, it is refused, or it is fatal.

        The two answers ``successors`` cannot give, because it reports only the first and one
        silence covers both the others. *Refused* is a wall — void, a closed bridge, a cell the
        other cube occupies — and carries no state, since nothing happened. *Fatal* is a fall, from
        a fragile tile breaking under a standing block (§2.5, ADR-003) or from a switch closing the
        bridge under the block (ADR-005), and carries the state the fall happens **in**: the block
        where it now is and the bridges as it now has them, so a renderer can animate both.

        That state is a rendering prop, not a state of play. It is exactly one ``successors``
        refuses to generate, so expanding it reaches nothing. Search never calls this.
        """
        verdict, next_state = self._resolve(state, *action)
        return Outcome(kind=verdict, state=next_state)

    def step_cost(self, state: State, action: Action, next_state: State) -> float:
        """One action costs one move. Weights are policy, not engine code (#7)."""
        return 1.0

    def passable(
        self, cell: Cell, orientation: Orientation, bridge_state: tuple[bool, ...]
    ) -> bool:
        """The only place passability is decided: one cell, one kind (§ Board)."""
        kind = self.kind(cell)
        if kind == "void":
            return False
        if kind == "bridge":
            return bridge_state[self._index.bridge_of[cell]]
        if kind == "fragile":
            return orientation != "standing"
        return True

    def is_goal(self, state: State) -> bool:
        """A standing block on the goal cell of an unsplit block (§2.4)."""
        return (
            len(state.cubes) == 1
            and len(state.cubes[0]) == 1
            and state.cubes[0][0] == self._index.goal
        )

    def kind(self, cell: Cell) -> Kind:
        """The kind of one cell. Anything off the board reads as void."""
        row, col = cell
        if not (0 <= row < self._index.rows and 0 <= col < self._index.cols):
            return "void"
        return self._index.kind[row * self._index.cols + col]

    def _resolve(
        self, state: State, index: int, direction: Direction
    ) -> tuple[Verdict, State | None]:
        """The one transition pipeline, and which of the three things it says happened.

        ``successors`` reads this and keeps only ``moves``; ``outcome`` reads all three. Because
        they share it, "fatal, and yet absent from ``successors``" cannot become false.

        The two fatal sites are disjoint by construction. A fragile tile gives way at the *first*
        passability check, and only for a single-cell result — a standing block, two units on one
        tile (§2.5, ADR-003). A bridge closing under the block is only visible *after* the switches
        fire, and needs the bridges to have changed (ADR-005). Neither can borrow the other's
        trigger: a standing piece on fragile occupies no bridge, and a merge always yields a lying
        block, which fragile accepts.
        """
        if index >= len(state.cubes):
            return "refused", None
        split = len(state.cubes) == 2
        before = set(cells(state))
        moved = roll(state.cubes[index], direction, split)
        if moved is None:
            return "refused", None
        cubes = [*state.cubes]
        cubes[index] = moved
        if not self._passable_cubes(cubes, state.bridges):
            if self._breaks_under_standing_load(cubes):
                return "fatal", State(cubes=tuple(cubes), bridges=state.bridges)
            return "refused", None
        if self._shares_a_cell(cubes):
            return "refused", None
        cubes, bridges = self._fire(cubes, list(state.bridges), set(moved) - before, before)
        cubes = _merge(cubes)
        if not self._passable_cubes(cubes, tuple(bridges)):
            if tuple(bridges) != state.bridges:
                return "fatal", State(cubes=tuple(cubes), bridges=tuple(bridges))
            return "refused", None
        if self._shares_a_cell(cubes):
            return "refused", None
        return "moves", State(cubes=tuple(cubes), bridges=tuple(bridges))

    def _breaks_under_standing_load(self, cubes: list[Cube]) -> bool:
        """True when the refusal that just happened is a fragile tile giving way (§2.5, ADR-003).

        Read as load, per ADR-003: an unsplit block on one cell is two units on one tile, and that
        is the only load fragile refuses. The predicate is exact, not "any cell is fragile": an
        unsplit standing result occupies exactly one cell, so when the passability check failed,
        that cell is the reason. A lying block spanning two fragile tiles still moves.
        """
        return len(cubes) == 1 and len(cubes[0]) == 1 and self.kind(cubes[0][0]) == "fragile"

    def _fire(
        self,
        cubes: list[Cube],
        bridges: list[bool],
        touched: set[Cell],
        before: set[Cell],
        *,
        allow_split: bool = True,
    ) -> tuple[list[Cube], list[bool]]:
        """Fire the switches the moved piece newly touches, not the ones it still stands on.

        A cube parked on a plate must not press it again when the other cube moves, and a switch the
        block was already sitting on fired on the move that put it there. A split's teleport targets
        count as contact once: a switch there may move a bridge, and a second split switch is
        ignored, so one action never chains (ADR-008).
        """
        split = len(cubes) == 2
        standing = not split and len(cubes[0]) == 1
        landed: set[Cell] | None = None
        for cell in sorted(touched):
            switch = self._index.switch_at.get(cell)
            if switch is None:
                continue
            if switch.type == "split":
                if allow_split and standing and switch.teleport_cubes is not None:
                    cubes = [(pos,) for pos in switch.teleport_cubes]
                    landed = {pos for pos in switch.teleport_cubes if pos not in before}
                    standing = False
                continue
            if switch.type == "heavy" and not standing:
                continue
            for pos in switch.bridges or ():
                slot = self._index.bridge_of[pos]
                bridges[slot] = _after_mode(switch.action, bridges[slot])
        if landed and allow_split:
            return self._fire(cubes, bridges, landed, before, allow_split=False)
        return cubes, bridges

    def _passable_cubes(self, cubes: list[Cube], bridges: tuple[bool, ...]) -> bool:
        split = len(cubes) == 2
        return all(
            self.passable(cell, orientation(cube, split), bridges)
            for cube in cubes
            for cell in cube
        )

    @staticmethod
    def _shares_a_cell(cubes: list[Cube]) -> bool:
        occupied = [cell for cube in cubes for cell in cube]
        return len(set(occupied)) != len(occupied)
