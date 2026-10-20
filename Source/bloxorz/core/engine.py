"""``Board``: the stage-scoped transition model (§ Board).

Transitions need stage data a state does not carry, so they hang off a board built from one stage.
``Board(stage)`` is O(1): the lookup tables were compiled by ``load_stage``.
"""

from __future__ import annotations

from bloxorz.core.contracts import Action, Cell, Cube, Direction, Kind, Orientation, Stage, State

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
        """
        found: list[tuple[State, Action]] = []
        for index in range(len(state.cubes)):
            for direction in DIRECTIONS:
                next_state = self._advance(state, index, direction)
                if next_state is not None:
                    found.append((next_state, (index, direction)))
        return found

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

    def is_fatal(self, state: State, action: Action) -> bool:
        """True when the action is legal except that it closes a bridge under the block (ADR-005).

        The renderer asks this to animate the fall that interactive play shows. Search never calls
        it, because ``successors`` drops the action instead.
        """
        index, direction = action
        if index >= len(state.cubes):
            return False
        split = len(state.cubes) == 2
        moved = roll(state.cubes[index], direction, split)
        if moved is None:
            return False
        cubes = [*state.cubes]
        cubes[index] = moved
        if not self._passable_cubes(cubes, state.bridges) or self._shares_a_cell(cubes):
            return False
        cubes, bridges = self._fire_switches(cubes, list(state.bridges))
        if tuple(bridges) == state.bridges:
            return False
        return not self._passable_cubes(_merge(cubes), tuple(bridges))

    def _advance(self, state: State, index: int, direction: Direction) -> State | None:
        split = len(state.cubes) == 2
        moved = roll(state.cubes[index], direction, split)
        if moved is None:
            return None
        cubes = [*state.cubes]
        cubes[index] = moved
        if not self._passable_cubes(cubes, state.bridges):
            return None
        if self._shares_a_cell(cubes):
            return None
        cubes, bridges = self._fire_switches(cubes, list(state.bridges))
        cubes = _merge(cubes)
        if not self._passable_cubes(cubes, tuple(bridges)):
            return None
        if self._shares_a_cell(cubes):
            return None
        return State(cubes=tuple(cubes), bridges=tuple(bridges))

    def _fire_switches(
        self, cubes: list[Cube], bridges: list[bool]
    ) -> tuple[list[Cube], list[bool]]:
        """Apply every switch the block touches. A split switch rewrites the cubes (ADR-008)."""
        split = len(cubes) == 2
        standing = not split and len(cubes[0]) == 1
        for cell in sorted(cell for cube in cubes for cell in cube):
            switch = self._index.switch_at.get(cell)
            if switch is None:
                continue
            if switch.type == "split":
                if standing and switch.teleport_cubes is not None:
                    cubes = [(pos,) for pos in switch.teleport_cubes]
                continue
            if switch.type == "heavy" and not standing:
                continue
            for pos in switch.bridges or ():
                slot = self._index.bridge_of[pos]
                bridges[slot] = not bridges[slot] if switch.type == "soft" else False
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
