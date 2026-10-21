"""Frozen v1 types, transcribed from ``docs/contracts.md``.

Types only: this module adds nothing beyond the three ``Stats`` properties that § Stats spells out.
Transitions live in ``engine.py``; the one way a stage enters the program is ``stage.load_stage``.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Literal

Cell = tuple[int, int]
Cube = tuple[Cell, ...]
Orientation = Literal["standing", "lying_h", "lying_v", "cube"]
Direction = Literal["U", "D", "L", "R"]
Action = tuple[int, Direction]
Kind = Literal["void", "floor", "start", "goal", "fragile", "bridge", "soft", "heavy", "split"]
Status = Literal["solved", "cap", "unsolvable"]


@dataclass(frozen=True)
class State:
    """The block, or two cubes after a split, plus one flag per stage bridge.

    The field set never varies with the value, so ``key()`` keeps arity 2 (#6).
    """

    cubes: tuple[Cube, ...]
    bridges: tuple[bool, ...]

    def key(self) -> tuple[object, ...]:
        """The state as a hashable tuple, derived from the fields so it cannot drift."""
        return tuple(getattr(self, field.name) for field in fields(self))

    def __post_init__(self) -> None:
        """Order the cubes canonically, by their cell, so one board has one spelling.

        The two cubes are interchangeable: nothing distinguishes them but their index. Without
        this, the same pair of occupied cells is reachable with the cubes in either order, those
        are two different ``key()`` values, and a visited set searches the position twice (#34).
        """
        if len(self.cubes) > 1:
            object.__setattr__(
                self, "cubes", tuple(sorted(self.cubes, key=lambda cube: min(cube)))
            )


@dataclass(frozen=True)
class Expected:
    """A hand-computed answer. Fixtures carry it; a solver never produces it."""

    optimal_cost: float


@dataclass(frozen=True)
class Switch:
    """One switch, wired at load time. Unused fields are ``None``, never absent."""

    type: Literal["soft", "heavy", "split"]
    pos: Cell
    action: Literal["toggle", "on", "off"] | None = None
    bridges: tuple[Cell, ...] | None = None
    teleport_cubes: tuple[Cell, Cell] | None = None


@dataclass(frozen=True)
class Bridge:
    """One bridge tile. ``State.bridges[i]`` is open when ``True``."""

    pos: Cell
    initially_open: bool = True


@dataclass(frozen=True)
class StageIndex:
    """Everything the grid already states, compiled once by ``load_stage``."""

    rows: int
    cols: int
    kind: tuple[Kind, ...]
    bridge_of: dict[Cell, int]
    switch_at: dict[Cell, Switch]
    start: Cell
    goal: Cell


@dataclass(frozen=True)
class Stage:
    """A loaded stage. ``index`` is derived, never trusted from the file."""

    id: str
    name: str
    group: str
    grid: tuple[str, ...]
    source: str | None
    expected: Expected | None
    index: StageIndex
    bridges: tuple[Bridge, ...]


@dataclass(frozen=True)
class Caps:
    """Search limits. ``Caps()`` means no limit."""

    node_cap: int | None = None
    time_s: float | None = None


@dataclass(frozen=True)
class Counts:
    """What the solver counts. No defaults: a missing metric fails loudly."""

    expanded: int
    generated: int
    frontier_peak: int


@dataclass(frozen=True)
class Stats:
    """The harness-built record of one algorithm-stage pair."""

    expanded: int
    generated: int
    frontier_peak: int
    time_s: float
    peak_mem_bytes: int

    @property
    def time_ms(self) -> float:
        return self.time_s * 1000.0

    @property
    def peak_mem_kb(self) -> float:
        return self.peak_mem_bytes / 1024.0

    @property
    def peak_mem_mb(self) -> float:
        return self.peak_mem_bytes / (1024.0 * 1024.0)


@dataclass(frozen=True)
class SearchResult:
    """The value ``solve()`` returns on every outcome."""

    status: Status
    path: tuple[Action, ...]
    cost: float
    counts: Counts
