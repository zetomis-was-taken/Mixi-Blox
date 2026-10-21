"""A* search with an admissible, mechanics-aware fallback heuristic."""

from __future__ import annotations

from bloxorz.core.contracts import Caps, SearchResult, Stage, State
from bloxorz.core.costs import MINIMUM_ACTION_COST
from bloxorz.core.engine import cells
from bloxorz.solvers.base import Heuristic, solve_search


def heuristic(stage: Stage, state: State) -> float:
    """A lower bound on remaining cost under issue #7's cost invariant.

    Without split switches, one roll can reduce the Manhattan distance of an
    occupied cell to the goal by at most two, hence ``distance * c_min / 2``.
    A split switch can teleport a cube arbitrarily far, invalidating any purely
    geometric lower bound; on such stages the proven admissible fallback is 0.
    """
    return make_heuristic(stage)(state)


def make_heuristic(stage: Stage) -> Heuristic:
    """Inspect static stage data once, outside the per-node heuristic calls."""
    if "split" in stage.index.kind:
        return lambda _state: 0.0
    goal_row, goal_col = stage.index.goal

    def estimate(state: State) -> float:
        distance = min(abs(row - goal_row) + abs(col - goal_col) for row, col in cells(state))
        return distance * MINIMUM_ACTION_COST / 2.0

    return estimate


def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult:
    """Return a minimum-total-cost solution using A*."""
    return solve_search(stage, caps, heuristic=make_heuristic(stage))
